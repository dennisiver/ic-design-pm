"""專案新增/編輯對話框"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from constants import FONT_BODY, FONT_BODY_BOLD


class ProjectDialog:
    def __init__(self, parent, db, project=None):
        self.db = db
        self.project = project
        self.result = False

        self.win = tk.Toplevel(parent)
        self.win.title("編輯專案" if project else "新增專案")
        self.win.geometry("400x250")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        main_frame = ttk.Frame(self.win, padding=16)
        main_frame.pack(fill='both', expand=True)

        # 專案名稱
        ttk.Label(main_frame, text="專案名稱: *", font=FONT_BODY_BOLD).pack(anchor='w')
        self.name_var = tk.StringVar(value=project.name if project else '')
        ttk.Entry(main_frame, textvariable=self.name_var,
                  font=FONT_BODY).pack(fill='x', pady=(0, 12))

        # 描述
        ttk.Label(main_frame, text="描述:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.desc_text = tk.Text(main_frame, height=4, font=FONT_BODY, wrap='word')
        self.desc_text.pack(fill='x', pady=(0, 12))
        if project and project.description:
            self.desc_text.insert('1.0', project.description)

        # 按鈕
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="取消", command=self.win.destroy,
                   style='Toolbar.TButton').pack(side='right', padx=(8, 0))
        ttk.Button(btn_frame, text="儲存", command=self._save,
                   style='Accent.TButton').pack(side='right')

        self.win.wait_window()

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("缺少必填欄位", "請輸入專案名稱", parent=self.win)
            return

        description = self.desc_text.get('1.0', 'end-1c').strip()

        if self.project:
            self.db.update_project(self.project.id, name, description,
                                   self.project.color)
        else:
            self.db.create_project(name, description)

        self.result = True
        self.win.destroy()
