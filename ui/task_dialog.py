"""任務新增/編輯對話框"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import re
import os
from constants import (STATUSES, PRIORITIES, DEFAULT_CATEGORIES,
                       FONT_BODY, FONT_BODY_BOLD, FONT_HEADER, FONT_FAMILY)
from ui.date_picker import DateEntry


class TaskDialog:
    def __init__(self, parent, db, task=None, default_project_id=None):
        self.db = db
        self.task = task
        self.result = False

        self.win = tk.Toplevel(parent)
        self.win.title("編輯任務" if task else "新增任務")
        self.win.geometry("560x720")
        self.win.resizable(False, True)
        self.win.transient(parent)
        self.win.grab_set()

        # 主捲動容器
        outer = ttk.Frame(self.win)
        outer.pack(fill='both', expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        main_frame = ttk.Frame(canvas, padding=16)
        win_id = canvas.create_window((0, 0), window=main_frame, anchor='nw')
        main_frame.bind('<Configure>',
                        lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfigure(win_id, width=e.width))
        canvas.bind('<Enter>',
                    lambda e: canvas.bind_all('<MouseWheel>',
                        lambda ev: canvas.yview_scroll(
                            int(-1 * (ev.delta / 120)), 'units')))
        canvas.bind('<Leave>',
                    lambda e: canvas.unbind_all('<MouseWheel>'))

        # ── 專案選擇 ──
        ttk.Label(main_frame, text="所屬專案:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.project_var = tk.StringVar()
        projects = db.get_all_projects()
        self.project_map = {p.name: p.id for p in projects}
        project_names = list(self.project_map.keys())
        self.project_combo = ttk.Combobox(main_frame, textvariable=self.project_var,
                                          values=project_names, state='readonly',
                                          font=FONT_BODY)
        self.project_combo.pack(fill='x', pady=(0, 8))

        if task:
            proj = db.get_project_by_id(task.project_id)
            if proj and proj.name in self.project_map:
                self.project_var.set(proj.name)
        elif default_project_id:
            for name, pid in self.project_map.items():
                if pid == default_project_id:
                    self.project_var.set(name)
                    break
        if not self.project_var.get() and project_names:
            self.project_var.set(project_names[0])

        # ── 標題 ──
        ttk.Label(main_frame, text="標題: *", font=FONT_BODY_BOLD).pack(anchor='w')
        self.title_var = tk.StringVar(value=task.title if task else '')
        ttk.Entry(main_frame, textvariable=self.title_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 8))

        # ── 描述（支援超連結）──
        ttk.Label(main_frame, text="描述 (支援檔案路徑連結):",
                  font=FONT_BODY_BOLD).pack(anchor='w')
        self.desc_text = tk.Text(main_frame, height=4, font=FONT_BODY, wrap='word')
        self.desc_text.pack(fill='x', pady=(0, 8))
        if task and task.description:
            self.desc_text.insert('1.0', task.description)
            self._highlight_links(self.desc_text)
        self.desc_text.bind('<KeyRelease>',
                            lambda e: self._highlight_links(self.desc_text))

        # ── 狀態 + 優先級 ──
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill='x', pady=(0, 8))
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=1)

        ttk.Label(mid_frame, text="狀態:", font=FONT_BODY_BOLD).grid(
            row=0, column=0, sticky='w')
        self.status_var = tk.StringVar(value=task.status if task else '待辦')
        ttk.Combobox(mid_frame, textvariable=self.status_var,
                     values=STATUSES, state='readonly',
                     font=FONT_BODY).grid(row=1, column=0, sticky='ew', padx=(0, 8))

        ttk.Label(mid_frame, text="優先級:", font=FONT_BODY_BOLD).grid(
            row=0, column=1, sticky='w')
        self.priority_var = tk.StringVar(value=task.priority if task else '中')
        ttk.Combobox(mid_frame, textvariable=self.priority_var,
                     values=PRIORITIES, state='readonly',
                     font=FONT_BODY).grid(row=1, column=1, sticky='ew')

        # ── 類別 + 負責人 ──
        mid2 = ttk.Frame(main_frame)
        mid2.pack(fill='x', pady=(0, 8))
        mid2.columnconfigure(0, weight=1)
        mid2.columnconfigure(1, weight=1)

        ttk.Label(mid2, text="類別:", font=FONT_BODY_BOLD).grid(
            row=0, column=0, sticky='w')
        self.category_var = tk.StringVar(value=task.category if task else '')
        db_cats = db.get_unique_categories()
        all_cats = sorted(set(DEFAULT_CATEGORIES + db_cats))
        ttk.Combobox(mid2, textvariable=self.category_var,
                     values=[''] + all_cats,
                     font=FONT_BODY).grid(row=1, column=0, sticky='ew', padx=(0, 8))

        ttk.Label(mid2, text="負責人:", font=FONT_BODY_BOLD).grid(
            row=0, column=1, sticky='w')
        self.assignee_var = tk.StringVar(value=task.assignee if task else '')
        assignees = db.get_unique_assignees()
        ttk.Combobox(mid2, textvariable=self.assignee_var,
                     values=assignees, font=FONT_BODY).grid(
            row=1, column=1, sticky='ew')

        # ── 日期與週數（使用日曆選擇器）──
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill='x', pady=(0, 8))
        date_frame.columnconfigure(0, weight=1)
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(2, weight=1)

        ttk.Label(date_frame, text="到期日:", font=FONT_BODY_BOLD).grid(
            row=0, column=0, sticky='w')
        self.due_var = tk.StringVar(
            value=task.due_date if task and task.due_date else '')
        DateEntry(date_frame, textvariable=self.due_var).grid(
            row=1, column=0, sticky='ew', padx=(0, 8))

        ttk.Label(date_frame, text="開始日期:", font=FONT_BODY_BOLD).grid(
            row=0, column=1, sticky='w')
        self.start_var = tk.StringVar(
            value=task.start_date if task and task.start_date else '')
        DateEntry(date_frame, textvariable=self.start_var).grid(
            row=1, column=1, sticky='ew', padx=(0, 8))

        ttk.Label(date_frame, text="預估週數:", font=FONT_BODY_BOLD).grid(
            row=0, column=2, sticky='w')
        self.weeks_var = tk.StringVar(
            value=str(task.estimated_weeks) if task and task.estimated_weeks else '')
        ttk.Entry(date_frame, textvariable=self.weeks_var,
                  font=FONT_BODY, width=6).grid(row=1, column=2, sticky='ew')

        # ── 標籤 ──
        ttk.Label(main_frame, text="標籤 (以逗號分隔):", font=FONT_BODY_BOLD).pack(
            anchor='w', pady=(4, 0))
        self.tags_var = tk.StringVar(
            value=', '.join(task.tags) if task and task.tags else '')
        ttk.Entry(main_frame, textvariable=self.tags_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 8))

        # ── 工作日誌按鈕（僅編輯模式）──
        if task:
            sep = ttk.Separator(main_frame, orient='horizontal')
            sep.pack(fill='x', pady=(4, 8))
            log_count = len(db.get_work_logs(task.id))
            ttk.Button(main_frame,
                       text=f"\U0001f4dd 工作日誌 ({log_count} 筆)",
                       command=self._open_work_log,
                       style='Toolbar.TButton').pack(anchor='w', pady=(0, 8))

        # ── 按鈕 ──
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(8, 0))
        ttk.Button(btn_frame, text="取消", command=self.win.destroy,
                   style='Toolbar.TButton').pack(side='right', padx=(8, 0))
        ttk.Button(btn_frame, text="儲存", command=self._save,
                   style='Accent.TButton').pack(side='right')

        self.win.wait_window()

    def _open_work_log(self):
        from ui.work_log_dialog import WorkLogDialog
        WorkLogDialog(self.win, self.db, self.task.id,
                      task_title=self.task.title)

    def _highlight_links(self, text_widget):
        """在 Text widget 中高亮檔案路徑和 URL"""
        # 先移除舊 tag
        for tag in text_widget.tag_names():
            if tag.startswith('link_'):
                text_widget.tag_remove(tag, '1.0', 'end')
                text_widget.tag_delete(tag)

        content = text_widget.get('1.0', 'end-1c')
        link_pattern = re.compile(
            r'(file:///[^\s]+|https?://[^\s]+|[A-Za-z]:\\[^\s,]+|\\\\[^\s,]+)')

        for match in link_pattern.finditer(content):
            # 計算 tkinter text index
            start_idx = f'1.0+{match.start()}c'
            end_idx = f'1.0+{match.end()}c'
            tag_name = f'link_{match.start()}'
            text_widget.tag_add(tag_name, start_idx, end_idx)
            text_widget.tag_configure(tag_name, foreground='#1565C0',
                                       underline=True)
            link = match.group(0)
            text_widget.tag_bind(tag_name, '<Button-1>',
                                  lambda e, p=link: self._open_link(p))
            text_widget.tag_bind(tag_name, '<Enter>',
                                  lambda e: text_widget.configure(
                                      cursor='hand2'))
            text_widget.tag_bind(tag_name, '<Leave>',
                                  lambda e: text_widget.configure(
                                      cursor='xterm'))

    def _open_link(self, path):
        """開啟本機檔案或 URL"""
        try:
            if path.startswith('http://') or path.startswith('https://'):
                import webbrowser
                webbrowser.open(path)
            elif path.startswith('file:///'):
                real_path = path.replace('file:///', '')
                os.startfile(real_path)
            else:
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("無法開啟", f"無法開啟：\n{path}\n\n{e}",
                                 parent=self.win)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("缺少必填欄位", "請輸入任務標題", parent=self.win)
            return

        project_name = self.project_var.get()
        if not project_name or project_name not in self.project_map:
            messagebox.showwarning("缺少必填欄位", "請選擇所屬專案", parent=self.win)
            return

        # 驗證日期格式
        due_date = self.due_var.get().strip() or None
        if due_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', due_date):
            messagebox.showwarning("格式錯誤", "到期日格式應為 YYYY-MM-DD",
                                   parent=self.win)
            return

        start_date = self.start_var.get().strip() or None
        if start_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', start_date):
            messagebox.showwarning("格式錯誤", "開始日期格式應為 YYYY-MM-DD",
                                   parent=self.win)
            return

        # 驗證預估週數
        weeks_str = self.weeks_var.get().strip()
        estimated_weeks = None
        if weeks_str:
            try:
                estimated_weeks = int(weeks_str)
                if estimated_weeks < 0:
                    messagebox.showwarning("格式錯誤", "預估週數不可為負數",
                                           parent=self.win)
                    return
            except ValueError:
                messagebox.showwarning("格式錯誤", "預估週數必須為整數",
                                       parent=self.win)
                return

        project_id = self.project_map[project_name]
        description = self.desc_text.get('1.0', 'end-1c').strip()
        status = self.status_var.get()
        priority = self.priority_var.get()
        category = self.category_var.get().strip()
        assignee = self.assignee_var.get().strip()
        tags_text = self.tags_var.get().strip()
        tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []

        if self.task:
            self.db.update_task(
                self.task.id, title, description, status, priority,
                category, assignee, due_date, start_date, estimated_weeks, tags)
        else:
            self.db.create_task(
                project_id, title, description, status, priority,
                category, assignee, due_date, start_date, estimated_weeks, tags)

        self.result = True
        self.win.destroy()
