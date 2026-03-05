"""工作日誌彈出視窗：左側週列表 + 右側日誌內容"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date, datetime, timedelta
import re
from collections import defaultdict
from constants import FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_FAMILY


class WorkLogDialog:
    def __init__(self, parent, db, task_id, task_title=''):
        self.db = db
        self.task_id = task_id

        self.win = tk.Toplevel(parent)
        self.win.title(f"工作日誌 - {task_title}")
        self.win.geometry("720x500")
        self.win.resizable(True, True)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        self._refresh()

        self.win.wait_window()

    def _build_ui(self):
        # 頂部工具列
        toolbar = ttk.Frame(self.win, padding=(8, 6))
        toolbar.pack(fill='x')

        ttk.Button(toolbar, text="+ 新增日誌",
                   command=self._add_log,
                   style='Accent.TButton').pack(side='left')

        total_frame = ttk.Frame(toolbar)
        total_frame.pack(side='right')
        ttk.Label(total_frame, text="總工時:", font=FONT_BODY).pack(side='left')
        self.total_label = ttk.Label(total_frame, text="0.0 h",
                                      font=FONT_BODY_BOLD)
        self.total_label.pack(side='left', padx=(4, 0))

        # 主區域：左右分割
        paned = ttk.PanedWindow(self.win, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=4, pady=4)

        # ─── 左側：週列表 ───
        left = ttk.Frame(paned)
        paned.add(left, weight=0)

        ttk.Label(left, text="週別", font=FONT_BODY_BOLD).pack(
            anchor='w', padx=8, pady=(4, 2))

        self.week_tree = ttk.Treeview(left, columns=('week', 'hours'),
                                       show='headings', height=15,
                                       selectmode='browse')
        self.week_tree.heading('week', text='日期範圍')
        self.week_tree.heading('hours', text='工時')
        self.week_tree.column('week', width=140, minwidth=120)
        self.week_tree.column('hours', width=60, minwidth=50)

        wsb = ttk.Scrollbar(left, orient='vertical',
                             command=self.week_tree.yview)
        self.week_tree.configure(yscrollcommand=wsb.set)
        self.week_tree.pack(side='left', fill='both', expand=True)
        wsb.pack(side='right', fill='y')

        self.week_tree.bind('<<TreeviewSelect>>', self._on_week_select)

        # ─── 右側：日誌明細 ───
        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        ttk.Label(right, text="日誌明細", font=FONT_BODY_BOLD).pack(
            anchor='w', padx=8, pady=(4, 2))

        self.detail_tree = ttk.Treeview(
            right, columns=('date', 'hours', 'content'),
            show='headings', height=15, selectmode='browse')
        self.detail_tree.heading('date', text='日期')
        self.detail_tree.heading('hours', text='工時')
        self.detail_tree.heading('content', text='內容')
        self.detail_tree.column('date', width=90, minwidth=80)
        self.detail_tree.column('hours', width=55, minwidth=45)
        self.detail_tree.column('content', width=320, minwidth=100)

        dsb = ttk.Scrollbar(right, orient='vertical',
                             command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=dsb.set)
        self.detail_tree.pack(side='left', fill='both', expand=True)
        dsb.pack(side='right', fill='y')

        self.detail_tree.bind('<Button-3>', self._on_right_click)

        self.week_data = {}   # iid -> (week_start, week_end)
        self.log_map = {}     # iid -> WorkLog
        self.all_logs = []

    # ─── 資料刷新 ──────────────────────────────────────────

    def _refresh(self):
        self.all_logs = self.db.get_work_logs(self.task_id)

        # 計算總工時
        total = sum(log.hours for log in self.all_logs)
        self.total_label.configure(text=f"{total:.1f} h")

        # 按週分組
        weeks = defaultdict(list)
        for log in self.all_logs:
            try:
                d = datetime.strptime(log.log_date, '%Y-%m-%d').date()
                # ISO 週一為週起始
                week_start = d - timedelta(days=d.weekday())
                weeks[week_start].append(log)
            except ValueError:
                # 無法解析的日期放在特殊組
                weeks[date(1900, 1, 1)].append(log)

        # 更新左側週列表
        self.week_tree.delete(*self.week_tree.get_children())
        self.week_data.clear()

        for week_start in sorted(weeks.keys(), reverse=True):
            logs = weeks[week_start]
            week_end = week_start + timedelta(days=6)
            week_hours = sum(l.hours for l in logs)

            if week_start == date(1900, 1, 1):
                label = '(其他)'
            else:
                label = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"

            iid = week_start.isoformat()
            self.week_tree.insert('', 'end', iid=iid,
                                  values=(label, f'{week_hours:.1f}h'))
            self.week_data[iid] = (week_start, logs)

        # 選擇第一週
        children = self.week_tree.get_children()
        if children:
            self.week_tree.selection_set(children[0])
            self._show_week_logs(children[0])

    def _on_week_select(self, event):
        sel = self.week_tree.selection()
        if sel:
            self._show_week_logs(sel[0])

    def _show_week_logs(self, week_iid):
        self.detail_tree.delete(*self.detail_tree.get_children())
        self.log_map.clear()

        data = self.week_data.get(week_iid)
        if not data:
            return

        _, logs = data
        for log in sorted(logs, key=lambda l: l.log_date, reverse=True):
            iid = str(log.id)
            self.detail_tree.insert('', 'end', iid=iid,
                                    values=(log.log_date,
                                            f'{log.hours:.1f}',
                                            log.content))
            self.log_map[iid] = log

    # ─── 新增日誌 ──────────────────────────────────────────

    def _add_log(self):
        _AddLogDialog(self.win, self.db, self.task_id,
                      on_save=self._refresh)

    # ─── 右鍵選單 ──────────────────────────────────────────

    def _on_right_click(self, event):
        item = self.detail_tree.identify_row(event.y)
        if not item or item not in self.log_map:
            return
        self.detail_tree.selection_set(item)

        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(label="刪除日誌",
                         command=lambda: self._delete_log(item))
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_log(self, iid):
        log = self.log_map.get(iid)
        if log and messagebox.askyesno("確認刪除", "確定要刪除此日誌？",
                                        parent=self.win):
            self.db.delete_work_log(log.id)
            self._refresh()


class _AddLogDialog:
    def __init__(self, parent, db, task_id, on_save=None):
        self.db = db
        self.task_id = task_id
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("新增工作日誌")
        self.win.geometry("380x280")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=12)
        f.pack(fill='both', expand=True)

        # 日期（用 DateEntry）
        ttk.Label(f, text="日期:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.date_var = tk.StringVar(value=date.today().isoformat())
        from ui.date_picker import DateEntry
        de = DateEntry(f, textvariable=self.date_var)
        de.pack(fill='x', pady=(0, 6))

        # 工時
        ttk.Label(f, text="工時 (小時):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.hours_var = tk.StringVar(value="1.0")
        ttk.Entry(f, textvariable=self.hours_var, font=FONT_BODY).pack(
            fill='x', pady=(0, 6))

        # 內容
        ttk.Label(f, text="內容:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.content_text = tk.Text(f, height=4, font=FONT_BODY, wrap='word')
        self.content_text.pack(fill='x', pady=(0, 8))

        bf = ttk.Frame(f)
        bf.pack(fill='x')
        ttk.Button(bf, text="取消", command=self.win.destroy,
                   style='Toolbar.TButton').pack(side='right', padx=(8, 0))
        ttk.Button(bf, text="儲存", command=self._save,
                   style='Accent.TButton').pack(side='right')

        self.win.wait_window()

    def _save(self):
        d = self.date_var.get().strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            messagebox.showwarning("格式錯誤", "日期格式應為 YYYY-MM-DD",
                                    parent=self.win)
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
