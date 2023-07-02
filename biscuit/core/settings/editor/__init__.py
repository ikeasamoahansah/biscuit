import tkinter as tk

from core.components.utils import ScrollableFrame
from core.components.editors.editor import BaseEditor

from .searchbar import Searchbar
from .section import Section


class SettingsEditor(BaseEditor):
    def __init__(self, master, exists=False, editable=False, *args, **kwargs):
        super().__init__(master, exists=exists, editable=editable, *args, **kwargs)
        self.config(padx=100, bg='white')
        self.filename = 'settings'

        #TODO searchbar functionality not implemented yet
        #NOTE: unpack the container and pack a new container for showing results
        self.search = Searchbar(self)
        self.search.pack(fill=tk.X, pady=20)

        self.sections = []
        self.container = ScrollableFrame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.add_sections()
    
    def add_sections(self):
        self.add_commonly_used()
        self.add_text_editor()

    def add_commonly_used(self):
        commonly_used = self.add_section(f"Commonly Used")
        commonly_used.add_dropdown("Color Theme", ("dark", "light"))
        commonly_used.add_intvalue("Font Size", 14)
        commonly_used.add_stringvalue("Font Family", "Consolas")
        commonly_used.add_intvalue("Tab Size", 4)

    def add_text_editor(self):
        commonly_used = self.add_section(f"Text Editor")
        commonly_used.add_checkbox("Auto Save", False)
        commonly_used.add_checkbox("Auto Closing Pairs", True)
        commonly_used.add_checkbox("Auto Closing Delete", True)
        commonly_used.add_checkbox("Auto Indent", True)
        commonly_used.add_checkbox("Auto Surround", True)
        commonly_used.add_checkbox("Word Wrap", False)
    
    def add_section(self, name):
        section = Section(self.container.content, name)
        section.pack(fill=tk.X, expand=True)
        self.sections.append(section)
        return section
    
    def show_result(self, items):
        if not any(items):
            return self.show_no_results()
    
    def show_no_results(self):
        ...