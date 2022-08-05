import tkinter as tk
from tkinter.constants import *

from .slots import Slots
from ....components.views.sidebar import *


class Sidebar(tk.Frame):
    """
    Vertically slotted container for views.

    +------+--------------------------+
    | Diry |    \    \    \    \    \ |
    +------+\    \    \    \    \    \|
    | Src  | \    \    \    \    \    |
    +------+  \    \    \    \    \   |
    | Git  |   \    \    \    \    \  |
    +------+    \    \    \    \    \ |
    |      |\    \    \    \    \    \|
    |      | \    \    \    \    \    |
    |      |  \    \    \    \    \   |
    +------+   \    \    \    \    \  |
    | Sett |    \    \    \    \    \ |
    +------+--------------------------+
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.base = master.base 

        self.slots = Slots(self)
        self.slots.pack(fill=Y, side=LEFT)

        self.active_view = None
        self.views = []

        self.default_views = [Explorer(self), Search(self), SourceControl(self)]
        self.add_views(self.default_views)

    def add_views(self, views):
        "Append views to list. Create tabs for them."
        for view in views:
            self.add_view(view)
    
    def add_view(self, view):
        "Appends a view to list. Create a tab."
        self.views.append(view)
        self.slots.add_slot(view)
        self.set_active_view(view)
        
    def delete_all_views(self):
        "Permanently delete all views."
        for view in self.views:
            view.destroy()

        self.views.clear()
    
    def delete_view(self, view):
        "Permanently delete a view."
        view.destroy()
        self.views.remove(view)
    
    def get_explorer(self):
        "Get explorer view."
        return self.default_views[0]

    def get_search(self):
        "Get search view."
        return self.default_views[1]

    def get_source_control(self):
        "Get source control view."
        return self.default_views[2]

    def set_active_view(self, view):
        "Set active view and active tab."
        self.active_view = view
        for _view in self.views:
            _view.pack_forget()
        view.pack(fill=BOTH, side=RIGHT, expand=1)
