"""側邊欄：專案資料夾樹狀列表"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from constants import FONT_HEADER, FONT_BODY


class ProjectSidebar(ttk.Frame):
    def __init__(self, parent, db, on_project_select, on_refresh):
        super().__init__(parent, width=220)
        self.db = db
        self.on_project_select = on_project_select
        self.on_refresh = on_refresh

        # 標題列
        header = ttk.Frame(self)
        header.pack(fill='x', padx=8, pady=(8, 4))
        ttk.Label(header, text="專案", font=FONT_HEADER).pack(side='left')
        ttk.Button(header, text="+", width=3,
                   command=self._new_project).pack(side='right')

        # 樹狀列表
        self.tree = ttk.Treeview(self, show='tree', selectmode='browse')
        self.tree.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        self.tree.insert('', 'end', iid='all', text='  全部專案', open=True)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Button-3>', self._on_right_click)

        self.refresh()

    def refresh(self):
        for child in self.tree.get_children('all'):
            self.tree.delete(child)

        projects = self.db.get_all_projects()
        for p in projects:
            self.tree.insert('all', 'end', iid=f'proj_{p.id}',
                             text=f'  \U0001F4C1 {p.name}')

        if not self.tree.selection():
            self.tree.selection_set('all')

    def _on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid == 'all':
            self.on_project_select(None)
        else:
            project_id = int(iid.replace('proj_', ''))
            self.on_project_select(project_id)

    def get_selected_project_id(self):
        selected = self.tree.selection()
        if not selected or selected[0] == 'all':
            return None
        return int(selected[0].replace('proj_', ''))

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item == 'all':
            return
        self.tree.selection_set(item)
        project_id = int(item.replace('proj_', ''))

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="重新命名",
                         command=lambda: self._rename_project(project_id))
        menu.add_separator()
        menu.add_command(label="刪除專案",
                         command=lambda: self._delete_project(project_id))
        menu.tk_popup(event.x_root, event.y_root)

    def _new_project(self):
        from ui.project_dialog import ProjectDialog
        dialog = ProjectDialog(self.winfo_toplevel(), self.db)
        if dialog.result:
            self.refresh()
            self.on_refresh()

    def _rename_project(self, project_id):
        from ui.project_dialog import ProjectDialog
        project = self.db.get_project_by_id(project_id)
        if project:
            dialog = ProjectDialog(self.winfo_toplevel(), self.db, project=project)
            if dialog.result:
                self.refresh()
                self.on_refresh()

    def _delete_project(self, project_id):
        project = self.db.get_project_by_id(project_id)
        if not project:
            return
        if messagebox.askyesno("確認刪除",
                               f"確定要刪除專案「{project.name}」？\n"
                               "此專案下的所有任務也將被刪除。"):
            self.db.delete_project(project_id)
            self.refresh()
            self.tree.selection_set('all')
            self.on_project_select(None)
            self.on_refresh()
