"""任務新增/編輯對話框"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import re
from constants import (STATUSES, PRIORITIES, IC_CATEGORIES,
                       FONT_BODY, FONT_BODY_BOLD, FONT_HEADER, FONT_FAMILY)


class TaskDialog:
    def __init__(self, parent, db, task=None, default_project_id=None):
        self.db = db
        self.task = task
        self.result = False

        self.win = tk.Toplevel(parent)
        self.win.title("編輯任務" if task else "新增任務")
        self.win.geometry("520x620")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        main_frame = ttk.Frame(self.win, padding=16)
        main_frame.pack(fill='both', expand=True)

        # 專案選擇
        ttk.Label(main_frame, text="所屬專案:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.project_var = tk.StringVar()
        projects = db.get_all_projects()
        self.project_map = {p.name: p.id for p in projects}
        project_names = list(self.project_map.keys())
        self.project_combo = ttk.Combobox(main_frame, textvariable=self.project_var,
                                          values=project_names, state='readonly',
                                          font=FONT_BODY)
        self.project_combo.pack(fill='x', pady=(0, 8))

        # 設定預設專案
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

        # 標題
        ttk.Label(main_frame, text="標題: *", font=FONT_BODY_BOLD).pack(anchor='w')
        self.title_var = tk.StringVar(value=task.title if task else '')
        ttk.Entry(main_frame, textvariable=self.title_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 8))

        # 描述
        ttk.Label(main_frame, text="描述:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.desc_text = tk.Text(main_frame, height=5, font=FONT_BODY, wrap='word')
        self.desc_text.pack(fill='x', pady=(0, 8))
        if task and task.description:
            self.desc_text.insert('1.0', task.description)

        # 中間欄位 - 兩欄排列
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill='x', pady=(0, 8))
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=1)

        # 狀態
        ttk.Label(mid_frame, text="狀態:", font=FONT_BODY_BOLD).grid(
            row=0, column=0, sticky='w')
        self.status_var = tk.StringVar(value=task.status if task else '待辦')
        ttk.Combobox(mid_frame, textvariable=self.status_var,
                     values=STATUSES, state='readonly',
                     font=FONT_BODY).grid(row=1, column=0, sticky='ew', padx=(0, 8))

        # 優先級
        ttk.Label(mid_frame, text="優先級:", font=FONT_BODY_BOLD).grid(
            row=0, column=1, sticky='w')
        self.priority_var = tk.StringVar(value=task.priority if task else '中')
        ttk.Combobox(mid_frame, textvariable=self.priority_var,
                     values=PRIORITIES, state='readonly',
                     font=FONT_BODY).grid(row=1, column=1, sticky='ew')

        # 類別 + 負責人
        mid2 = ttk.Frame(main_frame)
        mid2.pack(fill='x', pady=(0, 8))
        mid2.columnconfigure(0, weight=1)
        mid2.columnconfigure(1, weight=1)

        ttk.Label(mid2, text="類別:", font=FONT_BODY_BOLD).grid(
            row=0, column=0, sticky='w')
        self.category_var = tk.StringVar(value=task.category if task else '')
        ttk.Combobox(mid2, textvariable=self.category_var,
                     values=[''] + IC_CATEGORIES, state='readonly',
                     font=FONT_BODY).grid(row=1, column=0, sticky='ew', padx=(0, 8))

        ttk.Label(mid2, text="負責人:", font=FONT_BODY_BOLD).grid(
            row=0, column=1, sticky='w')
        self.assignee_var = tk.StringVar(value=task.assignee if task else '')
        assignees = db.get_unique_assignees()
        ttk.Combobox(mid2, textvariable=self.assignee_var,
                     values=assignees, font=FONT_BODY).grid(
            row=1, column=1, sticky='ew')

        # 到期日
        ttk.Label(main_frame, text="到期日 (YYYY-MM-DD):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.due_var = tk.StringVar(value=task.due_date if task and task.due_date else '')
        ttk.Entry(main_frame, textvariable=self.due_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 8))

        # 標籤
        ttk.Label(main_frame, text="標籤 (以逗號分隔):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.tags_var = tk.StringVar(
            value=', '.join(task.tags) if task and task.tags else '')
        ttk.Entry(main_frame, textvariable=self.tags_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 12))

        # 按鈕
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="取消", command=self.win.destroy,
                   style='Toolbar.TButton').pack(side='right', padx=(8, 0))
        ttk.Button(btn_frame, text="儲存", command=self._save,
                   style='Accent.TButton').pack(side='right')

        self.win.wait_window()

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("缺少必填欄位", "請輸入任務標題", parent=self.win)
            return

        project_name = self.project_var.get()
        if not project_name or project_name not in self.project_map:
            messagebox.showwarning("缺少必填欄位", "請選擇所屬專案", parent=self.win)
            return

        due_date = self.due_var.get().strip() or None
        if due_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', due_date):
            messagebox.showwarning("格式錯誤", "到期日格式應為 YYYY-MM-DD",
                                   parent=self.win)
            return

        project_id = self.project_map[project_name]
        description = self.desc_text.get('1.0', 'end-1c').strip()
        status = self.status_var.get()
        priority = self.priority_var.get()
        category = self.category_var.get()
        assignee = self.assignee_var.get().strip()
        tags_text = self.tags_var.get().strip()
        tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []

        if self.task:
            self.db.update_task(
                self.task.id, title, description, status, priority,
                category, assignee, due_date, tags)
        else:
            self.db.create_task(
                project_id, title, description, status, priority,
                category, assignee, due_date, tags)

        self.result = True
        self.win.destroy()
