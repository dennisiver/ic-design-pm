"""里程碑管理對話框"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import re
from constants import FONT_BODY, FONT_BODY_BOLD, FONT_HEADER


class MilestoneDialog:
    def __init__(self, parent, db, project_id, project_name=''):
        self.db = db
        self.project_id = project_id
        self.result = False

        self.win = tk.Toplevel(parent)
        self.win.title(f"管理里程碑 - {project_name}")
        self.win.geometry("500x400")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=12)
        f.pack(fill='both', expand=True)

        # 里程碑列表
        cols = ('name', 'date', 'desc')
        self.tree = ttk.Treeview(f, columns=cols, show='headings', height=8)
        self.tree.heading('name', text='名稱')
        self.tree.heading('date', text='目標日期')
        self.tree.heading('desc', text='說明')
        self.tree.column('name', width=120)
        self.tree.column('date', width=100)
        self.tree.column('desc', width=220)
        self.tree.pack(fill='both', expand=True, pady=(0, 8))

        self.ms_map = {}

        # 按鈕列
        bf = ttk.Frame(f)
        bf.pack(fill='x')
        ttk.Button(bf, text="+ 新增", command=self._add).pack(side='left', padx=(0, 4))
        ttk.Button(bf, text="編輯", command=self._edit).pack(side='left', padx=(0, 4))
        ttk.Button(bf, text="刪除", command=self._delete).pack(side='left')
        ttk.Button(bf, text="關閉", command=self._close).pack(side='right')

        self._refresh()
        self.win.wait_window()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.ms_map.clear()
        for ms in self.db.get_milestones(self.project_id):
            iid = str(ms.id)
            self.tree.insert('', 'end', iid=iid,
                             values=(ms.name, ms.target_date, ms.description))
            self.ms_map[iid] = ms

    def _add(self):
        _MilestoneEditDialog(self.win, self.db, self.project_id,
                             on_save=self._on_change)

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        ms = self.ms_map.get(sel[0])
        if ms:
            _MilestoneEditDialog(self.win, self.db, self.project_id,
                                 milestone=ms, on_save=self._on_change)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        ms = self.ms_map.get(sel[0])
        if ms and messagebox.askyesno("確認刪除",
                                       f"確定要刪除里程碑「{ms.name}」？",
                                       parent=self.win):
            self.db.delete_milestone(ms.id)
            self._on_change()

    def _on_change(self):
        self.result = True
        self._refresh()

    def _close(self):
        self.win.destroy()


class _MilestoneEditDialog:
    def __init__(self, parent, db, project_id, milestone=None, on_save=None):
        self.db = db
        self.project_id = project_id
        self.milestone = milestone
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("編輯里程碑" if milestone else "新增里程碑")
        self.win.geometry("360x220")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=12)
        f.pack(fill='both', expand=True)

        ttk.Label(f, text="名稱:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.name_var = tk.StringVar(value=milestone.name if milestone else '')
        ttk.Entry(f, textvariable=self.name_var, font=FONT_BODY).pack(fill='x', pady=(0, 6))

        ttk.Label(f, text="目標日期 (YYYY-MM-DD):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.date_var = tk.StringVar(
            value=milestone.target_date if milestone else '')
        ttk.Entry(f, textvariable=self.date_var, font=FONT_BODY).pack(fill='x', pady=(0, 6))

        ttk.Label(f, text="說明:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.desc_var = tk.StringVar(
            value=milestone.description if milestone else '')
        ttk.Entry(f, textvariable=self.desc_var, font=FONT_BODY).pack(fill='x', pady=(0, 8))

        bf = ttk.Frame(f)
        bf.pack(fill='x')
        ttk.Button(bf, text="取消", command=self.win.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(bf, text="儲存", command=self._save).pack(side='right')

        self.win.wait_window()

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("缺少必填", "請輸入名稱", parent=self.win)
            return
        d = self.date_var.get().strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            messagebox.showwarning("格式錯誤", "日期格式應為 YYYY-MM-DD", parent=self.win)
            return
        desc = self.desc_var.get().strip()
        if self.milestone:
            self.db.update_milestone(self.milestone.id, name, d, desc)
        else:
            self.db.create_milestone(self.project_id, name, d, desc)
        if self.on_save:
            self.on_save()
        self.win.destroy()
