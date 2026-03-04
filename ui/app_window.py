"""主視窗：工具列 + 側邊欄 + 主內容區 + 狀態列"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from constants import (IC_CATEGORIES, PRIORITIES, FONT_BODY, FONT_BODY_BOLD,
                       FONT_HEADER, FONT_FAMILY, APP_NAME)
from ui.styles import setup_styles
from ui.sidebar import ProjectSidebar
from ui.kanban_view import KanbanView
from ui.list_view import ListView
from ui.task_dialog import TaskDialog


class AppWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.current_project_id = None
        self.current_view = 'kanban'
        self.filter_state = {
            'search': '',
            'category': None,
            'priority': None,
            'assignee': None,
        }
        self._debounce_id = None

        setup_styles(root)
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

        self.refresh_all()

    # ─── 工具列 ─────────────────────────────────────────────

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=(8, 6))
        toolbar.pack(fill='x', side='top')

        # 新增任務按鈕
        ttk.Button(toolbar, text="\u2795 新增任務",
                   command=self._new_task,
                   style='Accent.TButton').pack(side='left', padx=(0, 8))

        # 匯出 Excel
        ttk.Button(toolbar, text="\U0001F4E5 匯出Excel",
                   command=self._export_excel,
                   style='Toolbar.TButton').pack(side='left', padx=(0, 16))

        # 搜尋框
        ttk.Label(toolbar, text="搜尋:", font=FONT_BODY).pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var,
                                 width=20, font=FONT_BODY)
        search_entry.pack(side='left', padx=(4, 12))
        search_entry.bind('<KeyRelease>', self._on_search_key)

        # 類別篩選
        ttk.Label(toolbar, text="類別:", font=FONT_BODY).pack(side='left')
        self.cat_filter_var = tk.StringVar(value='全部')
        cat_combo = ttk.Combobox(toolbar, textvariable=self.cat_filter_var,
                                 values=['全部'] + IC_CATEGORIES,
                                 state='readonly', width=18, font=FONT_BODY)
        cat_combo.pack(side='left', padx=(4, 12))
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # 優先級篩選
        ttk.Label(toolbar, text="優先級:", font=FONT_BODY).pack(side='left')
        self.pri_filter_var = tk.StringVar(value='全部')
        pri_combo = ttk.Combobox(toolbar, textvariable=self.pri_filter_var,
                                 values=['全部'] + PRIORITIES,
                                 state='readonly', width=8, font=FONT_BODY)
        pri_combo.pack(side='left', padx=(4, 12))
        pri_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # 視圖切換
        self.view_var = tk.StringVar(value='kanban')
        ttk.Radiobutton(toolbar, text="看板", variable=self.view_var,
                        value='kanban',
                        command=self._switch_view).pack(side='right', padx=4)
        ttk.Radiobutton(toolbar, text="列表", variable=self.view_var,
                        value='list',
                        command=self._switch_view).pack(side='right', padx=4)

    # ─── 主內容區 ───────────────────────────────────────────

    def _build_main_area(self):
        paned = ttk.PanedWindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=4, pady=4)

        # 側邊欄
        self.sidebar = ProjectSidebar(
            paned, self.db,
            on_project_select=self._on_project_select,
            on_refresh=self.refresh_all
        )
        paned.add(self.sidebar, weight=0)

        # 內容區容器
        self.content_frame = ttk.Frame(paned)
        paned.add(self.content_frame, weight=1)

        # 看板視圖
        self.kanban_view = KanbanView(
            self.content_frame,
            on_task_click=self._on_task_click,
            on_status_change=self._on_status_change,
            on_task_delete=self._on_task_delete
        )

        # 列表視圖
        self.list_view = ListView(
            self.content_frame,
            on_task_click=self._on_task_click,
            on_status_change=self._on_status_change,
            on_task_delete=self._on_task_delete
        )

        # 預設顯示看板
        self.kanban_view.pack(fill='both', expand=True)

    # ─── 狀態列 ─────────────────────────────────────────────

    def _build_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="", style='Status.TLabel',
                                   padding=(8, 4))
        self.statusbar.pack(fill='x', side='bottom')

    def _update_statusbar(self, count):
        project_name = "全部專案"
        if self.current_project_id:
            proj = self.db.get_project_by_id(self.current_project_id)
            if proj:
                project_name = proj.name
        self.statusbar.configure(
            text=f"共 {count} 項任務  |  專案: {project_name}")

    # ─── 中央刷新 ───────────────────────────────────────────

    def refresh_all(self):
        tasks = self.db.get_tasks(
            project_id=self.current_project_id,
            search=self.filter_state['search'] or None,
            category=self.filter_state['category'],
            priority=self.filter_state['priority'],
            assignee=self.filter_state['assignee'],
        )
        if self.current_view == 'kanban':
            self.kanban_view.refresh(tasks)
        else:
            self.list_view.refresh(tasks)
        self._update_statusbar(len(tasks))

    # ─── 回呼函式 ───────────────────────────────────────────

    def _on_project_select(self, project_id):
        self.current_project_id = project_id
        self.refresh_all()

    def _on_task_click(self, task_id):
        task = self.db.get_task_by_id(task_id)
        if task:
            dialog = TaskDialog(self.root, self.db, task=task)
            if dialog.result:
                self.refresh_all()

    def _on_status_change(self, task_id, new_status):
        self.db.update_task_status(task_id, new_status)
        self.refresh_all()

    def _on_task_delete(self, task_id):
        task = self.db.get_task_by_id(task_id)
        if not task:
            return
        if messagebox.askyesno("確認刪除",
                               f"確定要刪除任務「{task.title}」？"):
            self.db.delete_task(task_id)
            self.refresh_all()

    def _new_task(self):
        dialog = TaskDialog(self.root, self.db,
                            default_project_id=self.current_project_id)
        if dialog.result:
            self.sidebar.refresh()
            self.refresh_all()

    # ─── 搜尋與篩選 ─────────────────────────────────────────

    def _on_search_key(self, event):
        if self._debounce_id:
            self.root.after_cancel(self._debounce_id)
        self._debounce_id = self.root.after(300, self._apply_filters)

    def _apply_filters(self):
        search = self.search_var.get().strip()
        cat = self.cat_filter_var.get()
        pri = self.pri_filter_var.get()

        self.filter_state['search'] = search
        self.filter_state['category'] = None if cat == '全部' else cat
        self.filter_state['priority'] = None if pri == '全部' else pri
        self.refresh_all()

    # ─── 視圖切換 ───────────────────────────────────────────

    def _switch_view(self):
        view = self.view_var.get()
        if view == self.current_view:
            return
        self.current_view = view
        if view == 'kanban':
            self.list_view.pack_forget()
            self.kanban_view.pack(fill='both', expand=True)
        else:
            self.kanban_view.pack_forget()
            self.list_view.pack(fill='both', expand=True)
        self.refresh_all()

    # ─── Excel 匯出 ─────────────────────────────────────────

    def _export_excel(self):
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="匯出 Excel",
            defaultextension='.xlsx',
            filetypes=[('Excel 檔案', '*.xlsx')],
            initialfile='任務清單.xlsx'
        )
        if not filepath:
            return

        tasks = self.db.get_tasks(
            project_id=self.current_project_id,
            search=self.filter_state['search'] or None,
            category=self.filter_state['category'],
            priority=self.filter_state['priority'],
        )

        project_name = "全部專案"
        if self.current_project_id:
            proj = self.db.get_project_by_id(self.current_project_id)
            if proj:
                project_name = proj.name

        try:
            from export import export_tasks_to_excel
            export_tasks_to_excel(filepath, tasks, project_name)
            messagebox.showinfo("匯出成功",
                                f"已匯出 {len(tasks)} 項任務至:\n{filepath}",
                                parent=self.root)
        except ImportError:
            messagebox.showerror("匯出失敗",
                                 "缺少 openpyxl 套件，請執行:\npip install openpyxl",
                                 parent=self.root)
        except Exception as e:
            messagebox.showerror("匯出失敗", str(e), parent=self.root)

    # ─── 關閉 ───────────────────────────────────────────────

    def on_close(self):
        self.db.close()
        self.root.destroy()
