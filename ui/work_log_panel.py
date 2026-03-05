"""工作日誌面板：嵌入任務對話框中"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date
import re
from constants import FONT_BODY, FONT_BODY_BOLD, FONT_SMALL


class WorkLogPanel(ttk.Frame):
    def __init__(self, parent, db, task_id):
        super().__init__(parent)
        self.db = db
        self.task_id = task_id

        header = ttk.Frame(self)
        header.pack(fill='x', pady=(4, 2))
        ttk.Label(header, text="工作日誌", font=FONT_BODY_BOLD).pack(side='left')
        ttk.Button(header, text="+ 新增日誌", width=10,
                   command=self._add_log).pack(side='right')

        cols = ('date', 'hours', 'content')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=5)
        self.tree.heading('date', text='日期')
        self.tree.heading('hours', text='時數')
        self.tree.heading('content', text='內容')
        self.tree.column('date', width=90, minwidth=80)
        self.tree.column('hours', width=50, minwidth=40)
        self.tree.column('content', width=300, minwidth=100)

        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree.bind('<Button-3>', self._on_right_click)
        self.log_map = {}
        self.refresh_logs()

    def refresh_logs(self):
        self.tree.delete(*self.tree.get_children())
        self.log_map.clear()
        logs = self.db.get_work_logs(self.task_id)
        for log in logs:
            iid = str(log.id)
            self.tree.insert('', 'end', iid=iid,
                             values=(log.log_date, f'{log.hours:.1f}', log.content))
            self.log_map[iid] = log

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item not in self.log_map:
            return
        self.tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="刪除日誌",
                         command=lambda: self._delete_log(item))
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_log(self, iid):
        log = self.log_map.get(iid)
        if log and messagebox.askyesno("確認刪除", "確定要刪除此日誌？",
                                        parent=self.winfo_toplevel()):
            self.db.delete_work_log(log.id)
            self.refresh_logs()

    def _add_log(self):
        _AddLogDialog(self.winfo_toplevel(), self.db, self.task_id,
                      on_save=self.refresh_logs)


class _AddLogDialog:
    def __init__(self, parent, db, task_id, on_save=None):
        self.db = db
        self.task_id = task_id
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("新增工作日誌")
        self.win.geometry("360x240")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=12)
        f.pack(fill='both', expand=True)

        ttk.Label(f, text="日期 (YYYY-MM-DD):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(f, textvariable=self.date_var, font=FONT_BODY).pack(fill='x', pady=(0, 6))

        ttk.Label(f, text="工時 (小時):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.hours_var = tk.StringVar(value="1.0")
        ttk.Entry(f, textvariable=self.hours_var, font=FONT_BODY).pack(fill='x', pady=(0, 6))

        ttk.Label(f, text="內容:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.content_text = tk.Text(f, height=3, font=FONT_BODY, wrap='word')
        self.content_text.pack(fill='x', pady=(0, 8))

        bf = ttk.Frame(f)
        bf.pack(fill='x')
        ttk.Button(bf, text="取消", command=self.win.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(bf, text="儲存", command=self._save).pack(side='right')

    def _save(self):
        d = self.date_var.get().strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            messagebox.showwarning("格式錯誤", "日期格式應為 YYYY-MM-DD", parent=self.win)
            return
        try:
            hours = float(self.hours_var.get().strip())
        except ValueError:
            messagebox.showwarning("格式錯誤", "工時必須為數字", parent=self.win)
            return
        content = self.content_text.get('1.0', 'end-1c').strip()
        self.db.create_work_log(self.task_id, d, content, hours)
        if self.on_save:
            self.on_save()
        self.win.destroy()
