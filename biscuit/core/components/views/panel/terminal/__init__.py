import tkinter as tk

from .tabs import Tabs
from .terminals import Default
from ..panelview import PanelView


class Terminal(PanelView):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.__buttons__ = (('add',),('trash',))

        self.config(bg=self.base.theme.border)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.grid_propagate(False)

        self.tabs = Tabs(self)
        self.tabs.grid(row=0, column=1, padx=(1, 0), sticky=tk.NS)

        self.terminals = []

        self.default_terminals = [Default(self), Default(self)]
        self.add_terminals(self.default_terminals)

    def add_terminals(self, terminals):
        "Append terminals to list. Create tabs for them."
        for terminal in terminals:
            self.add_terminal(terminal)
    
    def add_terminal(self, terminal):
        "Appends a terminal to list. Create a tab."
        self.terminals.append(terminal)
        self.tabs.add_tab(terminal)

    def delete_all_terminals(self):
        "Permanently delete all terminals."
        for terminal in self.terminals:
            terminal.destroy()

        self.terminals.clear()
    
    def delete_terminal(self, terminal):
        "Permanently delete a terminal."
        terminal.destroy()
        self.terminals.remove(terminal)
    
    def set_active_terminal(self, terminal):
        "set an existing editor to currently shown one"
        for tab in self.tabs.tabs:
            if tab.terminal == terminal:
                self.tabs.set_active_tab(tab)
    
    @property
    def pwsh(self):
        return self.default_terminals[0]
    
    @property
    def cmd(self):
        return self.default_terminals[1]

    @property
    def python(self):
        return self.default_terminals[1]

    @property
    def active_editor(self):
        "Get active editor."
        if not self.tabs.active_tab:
            return
        
        return self.tabs.active_tab.editor
    
    def refresh(self):
        ...
        # if not len(self.editors) and self.empty:
        #     self.emptytab.grid()
        # elif len(self.editors) and not self.empty:
        #     self.emptytab.grid_remove()
        # self.empty = not self.empty
