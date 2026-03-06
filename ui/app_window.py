"""主視窗：工具列 + 側邊欄 + 主內容區（4視圖分頁）+ 狀態列"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from constants import (DEFAULT_CATEGORIES, PRIORITIES, FONT_BODY, FONT_BODY_BOLD,
                       FONT_HEADER, FONT_FAMILY, APP_NAME)
from ui.styles import setup_styles
from ui.sidebar import ProjectSidebar
from ui.kanban_view import KanbanView
from ui.list_view import ListView
from ui.gantt_view import GanttView
from ui.dashboard_view import DashboardView
from ui.task_dialog import TaskDialog


class AppWindow:
    VIEWS = ['kanban', 'list', 'gantt', 'dashboard']
    VIEW_LABELS = {
        'kanban': '📋 看板',
        'list': '📑 列表',
        'gantt': '📊 甘特圖',
        'dashboard': '📈 儀表板',
    }

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
        self._build_tab_bar()
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
                   style='Accent.TButton').pack(side='left', padx=(0, 4))

        # 匯出 Excel
        ttk.Button(toolbar, text="\U0001F4E5 匯出",
                   command=self._export_excel,
                   style='Toolbar.TButton').pack(side='left', padx=(0, 4))

        # 匯入 Excel
        ttk.Button(toolbar, text="\U0001F4E4 匯入",
                   command=self._import_excel,
                   style='Toolbar.TButton').pack(side='left', padx=(0, 16))

        # 搜尋框
        ttk.Label(toolbar, text="搜尋:", font=FONT_BODY).pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var,
                                 width=18, font=FONT_BODY)
        search_entry.pack(side='left', padx=(4, 12))
        search_entry.bind('<KeyRelease>', self._on_search_key)

        # 類別篩選（動態）
        ttk.Label(toolbar, text="類別:", font=FONT_BODY).pack(side='left')
        self.cat_filter_var = tk.StringVar(value='全部')
        self.cat_combo = ttk.Combobox(toolbar, textvariable=self.cat_filter_var,
                                       state='readonly', width=18, font=FONT_BODY)
        self.cat_combo.pack(side='left', padx=(4, 12))
        self.cat_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # 優先級篩選
        ttk.Label(toolbar, text="優先級:", font=FONT_BODY).pack(side='left')
        self.pri_filter_var = tk.StringVar(value='全部')
        pri_combo = ttk.Combobox(toolbar, textvariable=self.pri_filter_var,
                                 values=['全部'] + PRIORITIES,
                                 state='readonly', width=8, font=FONT_BODY)
        pri_combo.pack(side='left', padx=(4, 0))
        pri_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

    # ─── 分頁列 ───────────────────────────────────────────

    def _build_tab_bar(self):
        self.tab_frame = ttk.Frame(self.root)
        self.tab_frame.pack(fill='x', padx=4)

        self.tab_buttons = {}
        for view in self.VIEWS:
            btn = ttk.Button(
                self.tab_frame,
                text=self.VIEW_LABELS[view],
                command=lambda v=view: self._switch_view(v),
                style='Tab.TButton')
            btn.pack(side='left', padx=(0, 2), pady=(2, 0))
            self.tab_buttons[view] = btn

        # 初始高亮
        self._update_tab_styles()

    def _update_tab_styles(self):
        for view, btn in self.tab_buttons.items():
            if view == self.current_view:
                btn.configure(style='ActiveTab.TButton')
            else:
                btn.configure(style='Tab.TButton')

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

        # 甘特圖視圖
        self.gantt_view = GanttView(
            self.content_frame,
            on_task_click=self._on_task_click
        )

        # 儀表板視圖
        self.dashboard_view = DashboardView(
            self.content_frame,
            on_task_click=self._on_task_click
        )

        self.views = {
            'kanban': self.kanban_view,
            'list': self.list_view,
            'gantt': self.gantt_view,
            'dashboard': self.dashboard_view,
        }

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
        # 更新類別篩選下拉
        self._update_category_filter()

        tasks = self.db.get_tasks(
            project_id=self.current_project_id,
            search=self.filter_state['search'] or None,
            category=self.filter_state['category'],
            priority=self.filter_state['priority'],
            assignee=self.filter_state['assignee'],
        )

        if self.current_view == 'kanban':
            self.kanban_view.refresh(tasks)
        elif self.current_view == 'list':
            self.list_view.refresh(tasks)
        elif self.current_view == 'gantt':
            # 甘特圖需要里程碑和專案對照 — 顯示所有專案的 Milestone
            if self.current_project_id:
                milestones = self.db.get_milestones(self.current_project_id)
            else:
                milestones = self.db.get_milestones()  # 全部
            projects = self.db.get_all_projects()
            project_lookup = {p.id: p.name for p in projects}
            self.gantt_view.refresh(tasks, milestones, project_lookup)
        elif self.current_view == 'dashboard':
            stats = self.db.get_dashboard_stats(self.current_project_id)
            # 儀表板也需要所有里程碑
            if self.current_project_id:
                milestones = self.db.get_milestones(self.current_project_id)
            else:
                milestones = self.db.get_milestones()
            project_progress = self.db.get_project_progress()
            projects = self.db.get_all_projects()
            project_lookup = {p.id: p.name for p in projects}
            self.dashboard_view.refresh(tasks, stats, milestones,
                                        project_progress=project_progress,
                                        project_lookup=project_lookup)

        self._update_statusbar(len(tasks))

    def _update_category_filter(self):
        """動態更新類別篩選下拉清單"""
        db_cats = self.db.get_unique_categories()
        all_cats = sorted(set(DEFAULT_CATEGORIES + db_cats))
        self.cat_combo.configure(values=['全部'] + all_cats)

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

    def _switch_view(self, view):
        if view == self.current_view:
            return
        # 隱藏當前視圖
        self.views[self.current_view].pack_forget()
        self.current_view = view
        # 顯示新視圖
        self.views[view].pack(fill='both', expand=True)
        self._update_tab_styles()
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

        # 建立專案與標籤查詢表
        projects = self.db.get_all_projects()
        project_lookup = {p.id: p.name for p in projects}
        task_tags = self.db.get_task_tags_bulk()

        try:
            from export import export_tasks_to_excel
            export_tasks_to_excel(filepath, tasks, project_name,
                                  project_lookup=project_lookup,
                                  task_tags_lookup=task_tags,
                                  db=self.db)
            messagebox.showinfo("匯出成功",
                                f"已匯出 {len(tasks)} 項任務至:\n{filepath}",
                                parent=self.root)
        except ImportError:
            messagebox.showerror("匯出失敗",
                                 "缺少 openpyxl 套件，請執行:\npip install openpyxl",
                                 parent=self.root)
        except Exception as e:
            messagebox.showerror("匯出失敗", str(e), parent=self.root)

    # ─── Excel 匯入 ─────────────────────────────────────────

    def _import_excel(self):
        if not self.current_project_id:
            messagebox.showwarning("請先選擇專案",
                                    "匯入功能需要先在左側選擇目標專案",
                                    parent=self.root)
            return

        filepath = filedialog.askopenfilename(
            parent=self.root,
            title="匯入 Excel",
            filetypes=[('Excel 檔案', '*.xlsx')],
        )
        if not filepath:
            return

        try:
            from importer import import_tasks_from_excel
            count, errors = import_tasks_from_excel(
                filepath, self.db, self.current_project_id)

            if errors:
                error_msg = "\n".join(errors[:20])
                if len(errors) > 20:
                    error_msg += f"\n... 共 {len(errors)} 個錯誤"
                messagebox.showerror("匯入失敗", error_msg, parent=self.root)
            else:
                messagebox.showinfo("匯入成功",
                                    f"已匯入 {count} 項任務",
                                    parent=self.root)
                self.sidebar.refresh()
                self.refresh_all()
        except ImportError:
            messagebox.showerror("匯入失敗",
                                 "缺少 openpyxl 套件，請執行:\npip install openpyxl",
                                 parent=self.root)
        except Exception as e:
            messagebox.showerror("匯入失敗", str(e), parent=self.root)

    # ─── 關閉 ───────────────────────────────────────────────

    def on_close(self):
        self.db.close()
        self.root.destroy()
