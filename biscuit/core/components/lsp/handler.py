from __future__ import annotations

import pprint
import re
import typing

import sansio_lsp_client as lsp

from .data import *
from .utils import *

if typing.TYPE_CHECKING:
    from .client import LangServerClient

class EventHandler:
    def __init__(self, master: LangServerClient):
        self.master = master
        self.client = master.client
        self.base = master.base

    def process(self, e: lsp.Event) -> None:
        print("----", e.__class__.__name__.upper())
        
        if isinstance(e, lsp.Shutdown):
            self.client.exit()
            return
        
        if isinstance(e, lsp.LogMessage):
            print(e.type, e.message)
            return
        
        if isinstance(e, lsp.Initialized):
            pprint.pprint(e.capabilities)
            for tab in self.master.tabs_opened:
                self.master.open_tab(tab)
            return
        
        if isinstance(e, lsp.Completion):
            tab, req = self.master._autocomplete_req.pop(e.message_id)
            if tab not in self.master.tabs_opened:
                return

            before_cursor = tab.get(f"{req.cursor} linestart", req.cursor)
            match = re.fullmatch(r".*?(\w*)", before_cursor)
            prefix_len = len(match.group(1))
            tab.lsp_show_autocomplete(
                Completions(
                    id=req.id,
                    completions=[
                        Completion(
                            display_text=item.label,
                            replace_start=tab.index(f"{req.cursor} - {prefix_len} chars"),
                            replace_end=req.cursor,
                            replace_text=item.insertText or item.label,
                            filter_text=(item.filterText or item.insertText or item.label)[prefix_len:],
                            documentation=get_completion_item_doc(item),
                        )
                        for item in sorted(
                            e.completion_list.items,
                            key=(lambda item: item.sortText or item.label),
                        )
                    ],
                ),
            )
        
        if isinstance(e, lsp.PublishDiagnostics):
            matching_tabs = [
                tab
                for tab in self.master.tabs_opened
                if tab.path is not None and Path(tab.path).as_uri() == e.uri
            ]
            if not matching_tabs:
                return
            tab = matching_tabs[0]

            tab.lsp_diagnostics(
                Underlines(
                    id="diagnostics",
                    underline_list=[
                        Underline(
                            start=decode_position(diagnostic.range.start),
                            end=decode_position(diagnostic.range.end),
                            tooltip_text=f"{diagnostic.source}: {diagnostic.message}",
                            color=(
                                "red"
                                if diagnostic.severity == lsp.DiagnosticSeverity.ERROR
                                else "orange"
                            ),
                        )
                        for diagnostic in sorted(
                            e.diagnostics,
                            key=(lambda diagn: diagn.severity or lsp.DiagnosticSeverity.WARNING),
                            reverse=True,
                        )
                    ],
                ),
            )
        
        if isinstance(e, lsp.Definition):
            tab = self.master._gotodef_requests.pop(e.message_id)

            tab.lsp_goto_definition(
                Jump(
                    [
                        JumpLocationRange(
                            file_path=str(path),
                            start=decode_position(range.start),
                            end=decode_position(range.end),
                        )
                        for path, range in jump_paths_and_ranges(e.result)
                    ]
                ),
            )
            return

        if isinstance(e, lsp.Hover):
            requesting_tab, location = self.master._hover_requests.pop(e.message_id)
            requesting_tab.lsp_hover(Hover(location, filter_hover_content(e.contents)))
            return