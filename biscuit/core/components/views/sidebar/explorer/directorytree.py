import os
import platform
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter.messagebox import askyesno

import pyperclip

from biscuit.core.components.floating.palette.actionset import ActionSet
from biscuit.core.utils import Tree

from ..item import SidebarViewItem
from .menu import ExplorerContextMenu
from .placeholder import DirectoryTreePlaceholder
from .watcher import DirectoryTreeWatcher


class DirectoryTree(SidebarViewItem):
    def __init__(self, master, startpath=None, observe_changes=False, itembar=True, *args, **kwargs) -> None:
        self.title = 'No folder opened'
        self.__buttons__ = (('new-file', lambda: self.base.palette.show('newfile:')), 
                            ('new-folder', lambda: self.base.palette.show('newfolder:')), 
                            ('refresh', self.refresh_root), ('collapse-all', self.collapse_all))
        super().__init__(master, itembar, *args, **kwargs)

        self.nodes = {}

        self.ignore_dirs = [".git", "__pycache__", ".pytest_cache", "node_modules", "debug", "dist", "build"]
        self.ignore_dir_patterns = ["*/.git/*", "*/__pycache__/*", "*/.pytest_cache/*", "*/node_modules/*", "*/debug/*", "*/dist/*", "*/build/*"]
        self.ignore_exts = [".pyc"]

        self.tree = Tree(self.content, startpath, doubleclick=self.openfile, singleclick=self.preview_file, *args, **kwargs)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.tree.grid_remove()
        self.tree.bind("<<Open>>", self.toggle_node)

        self.placeholder = DirectoryTreePlaceholder(self.content)
        self.placeholder.grid(row=0, column=0, sticky=tk.NSEW)

        self.path = startpath
        self.watcher = DirectoryTreeWatcher(self, self.tree, observe_changes)
        self.loading = False

        self.ctxmenu = ExplorerContextMenu(self, "ExplorerContextMenu")
        self.tree.bind('<Button-3>', self.right_click)

        if startpath:
            self.change_path(startpath)
        else:
            self.tree.insert('', 0, text='You have not yet opened a folder.')
    
    def right_click(self, e: tk.Event) -> None:
        """Shows the context menu on right click."""
        
        if item := self.tree.identify_row(e.y):
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.ctxmenu.show(e)

    # IMPORTANT
    def change_path(self, path: str) -> None:
        """Changes the current directory and updates the treeview.
        Main interface for changing the current directory and updating the treeview."""

        self.nodes.clear()
        self.path = os.path.abspath(path) if path else path
        self.nodes[self.path] = ''
        if self.path:
            self.placeholder.grid_remove()
            self.tree.grid()
            self.tree.clear_tree()
            self.create_root(self.path, subdir=False)
            self.watcher.watch()

            self.set_title(os.path.basename(self.path))
        else:
            self.tree.grid_remove()
            self.placeholder.grid()
            self.set_title('No folder opened')

    def create_root(self, path: str, parent='', subdir=True) -> None:
        """Creates the root node of the treeview."""

        if self.loading:
            return

        self.loading = True
        t = threading.Thread(target=self.run_create_sub_root if subdir else self.run_create_root, args=(path, parent))
        t.daemon = True
        t.start()

    def run_create_root(self, path: str, parent='') -> None:
        """Updates the treeview with the contents of the given directory."""

        self.update_treeview(path, parent)
        self.loading = False
    
    def run_create_sub_root(self, path: str, parent='') -> None:
        """Updates the treeview with the contents of the given directory."""

        self.update_treeview(path, parent)
        self.loading = False

    def get_all_files(self) -> list:
        """Returns a list of all files in the treeview."""

        files = []
        for item in self.tree.get_children():
            if self.tree.item_type(item) == 'file':
                files.append((self.tree.item(item, "text"), lambda _, item=item: print(self.tree.item_fullpath(item))))

        return files

    def scandir(self, path) -> list:
        """Returns a list of entries in the given directory.
        Heloper function for updating the treeview."""

        entries = []
        for entry in os.scandir(path):
            entries.append((entry.name, os.path.join(self.path, entry.path)))
        return entries

    def update_path(self, path) -> None:
        """Updates the treeview with the contents of the given directory."""

        if not path or any(path.endswith(i) for i in self.ignore_dirs):
            return

        node = self.nodes.get(os.path.abspath(path)) 
        for i in self.tree.get_children(node):
            self.tree.delete(i)

        self.create_root(path, node)

    def update_treeview(self, parent_path, parent="") -> None:
        """Updates the treeview with the contents of the given directory."""

        if not os.path.exists(parent_path):
            return

        entries = self.scandir(parent_path)
        # sort: directories first, then files (alphabetic order)
        entries.sort(key=lambda x: (not os.path.isdir(x[1]), x[0]))

        try:
            for name, path in entries:
                if os.path.isdir(path):
                    if name in self.ignore_dirs:
                        continue

                    node = self.tree.insert(parent, "end", text=f"  {name}", values=[path, 'directory'], image='foldericon', open=False)
                    self.nodes[os.path.abspath(path)] = node
                    self.tree.insert(node, "end", text="loading...")

                    # recursive mode loading (not good for large projects)
                    #self.update_treeview(path, node)
                else:
                    if name.split(".")[-1] in self.ignore_exts:
                        continue

                    #TODO check filetype and get matching icon, cases
                    node = self.tree.insert(parent, "end", text=f"  {name}", values=[path, 'file'], image='document')
                    self.nodes[os.path.abspath(path)] = node
        except Exception as e:
            self.base.logger.error(f"Error updating treeview: {e}")

    def selected_directory(self) -> str:
        """Returns the selected directory path, or the current path if no directory is selected."""

        return (self.tree.selected_path().strip() if self.tree.selected_type() != 'file' else self.tree.selected_parent_path().strip()) or self.path

    def new_file(self, filename) -> None:
        """Creates a new file in the selected directory."""

        if not filename:
            return

        parent = self.selected_directory() or self.base.active_directory or os.path.abspath('.')
        path = os.path.join(parent, filename)

        if os.path.exists(path):
            # If user tries to create a new file with the name of an existing file
            # open that existing file in editor instead. 
            self.base.open_editor(path)
            return
        
        with open(path, 'w+') as f:
            f.write("")
        self.create_root(parent, self.nodes[parent])

    def new_folder(self, foldername) -> None:
        """Creates a new folder in the selected directory."""

        if not foldername:
            return

        parent = self.selected_directory()
        path = os.path.join(parent, foldername)
        try:
            os.makedirs(path, exist_ok=True)
        except:
            self.base.logger.error(f"Creating folder failed: no permission to write ('{path}')")
            self.base.notifications.error("Creating folder failed: see logs")
            return
        self.create_root(parent, self.nodes[parent])

    def copy_path(self, *_) -> None:
        """Copies the absolute path of the selected item to the clipboard."""

        pyperclip.copy(self.tree.selected_path())

    def copy_relpath(self, *_) -> None:
        """Copies the relative path of the selected item to the clipboard."""

        pyperclip.copy(os.path.relpath(self.tree.selected_path(), self.path))
    
    def reopen_editor(self, *_) -> None:
        """Reopens the selected file in the editor."""

        path = os.path.abspath(self.tree.selected_path())
        if self.tree.selected_type() == 'file':
            self.base.editorsmanager.reopen_editor(path)
            
    def reveal_in_explorer(self, *_) -> None:
        """Reveals the selected directory in the file explorer.
        
        This method is platform dependent, and uses the `subprocess` module 
        to open the file explorer. If the file explorer executable is not found,
        it will log the error and show a warning notification."""

        path = self.selected_directory()
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['start', path], shell=True)
            elif platform.system() == 'Linux':
                try:
                    subprocess.Popen(['xdg-open', path])
                except OSError:
                    subprocess.Popen(['nautilus', path, '&'])
            else:
                subprocess.Popen(['open', path])
        except OSError as e:
            self.base.notifications.warning("No File Explorer executable detected, see logs")
            self.base.logger.error(f"Explorer: {e}\n(Mostly because no File explorer executable detected)")
            return

    def open_in_terminal(self, *_) -> None:
        """Opens the selected directory in a terminal."""

        if path := self.selected_directory():
            self.base.terminalmanager.open_terminal(path)
            self.base.panel.show_panel()

    def rename_item(self, newname: str) -> None:
        """Renames the selected item in the treeview."""

        parent = self.tree.selected_parent_path()

        if path := self.tree.selected_path():
            shutil.move(path, os.path.join(self.tree.selected_parent_path() or self.path, newname))
        
        self.update_path(parent)

    def delete_item(self) -> None:
        """Deletes the selected item from the treeview."""

        path = self.tree.selected_path()
        parent = self.tree.selected_parent_path()
        if not askyesno("Delete", f"Are you sure of deleting {path}?"):
            return

        try:
            if self.tree.selected_type() == 'directory':
                shutil.rmtree(path)
                return
            os.remove(path)
        except OSError as e:
            self.base.notifications.warning("Removing failed, see logs")
            self.base.logger.error(f"Removing failed: {e}")
            return
        
        # refresh parent of the deleted item
        self.update_path(parent)

    def collapse_all(self, *_) -> None:
        """Collapses all nodes in the treeview."""

        for node in self.tree.get_children(''):
            self.tree.item(node, open=False)

    def refresh_selected_parent(self, *_) -> None:
        """Reloads entire parent node of the selected node."""

        self.update_path(self.tree.selected_parent_path())

    def refresh_root(self, *_) -> None:
        """Reloads entire treeview from the root."""

        self.update_path(self.path)

    def close_directory(self) -> None:
        """Closes the current directory and clears the treeview."""

        self.change_path(None)

    def toggle_node(self, *_) -> None:
        """Toggles the selected node, if it's a directory."""

        node = self.tree.focus()
        for i in self.tree.get_children(node):
            self.tree.delete(i)

        self.create_root(self.tree.selected_path(), node)

    def openfile(self, _) -> None:
        """Opens the selected file in an editor."""

        if self.tree.selected_type() != 'file':
            return

        path = self.tree.selected_path()
        self.base.open_editor(path)

    def preview_file(self, _) -> None:
        #TODO preview editors -- extra preview param for editors
        return

