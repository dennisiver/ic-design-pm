"""工作日誌彈出視窗：左側日期列表 + 右側日誌內容（同日期全部顯示）"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date, datetime, timedelta
import re
import os
from collections import defaultdict
from constants import FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_FAMILY


class WorkLogDialog:
    def __init__(self, parent, db, task_id, task_title=''):
        self.db = db
        self.task_id = task_id

        self.win = tk.Toplevel(parent)
        self.win.title(f"工作日誌 - {task_title}")
        self.win.geometry("800x560")
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
        self.total_label = ttk.Label(total_frame, text="0.0 天",
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

        self.week_tree = ttk.Treeview(left, columns=('week', 'days'),
                                       show='headings', height=18,
                                       selectmode='browse')
        self.week_tree.heading('week', text='日期範圍')
        self.week_tree.heading('days', text='工時(天)')
        self.week_tree.column('week', width=140, minwidth=120)
        self.week_tree.column('days', width=70, minwidth=50)

        wsb = ttk.Scrollbar(left, orient='vertical',
                             command=self.week_tree.yview)
        self.week_tree.configure(yscrollcommand=wsb.set)
        self.week_tree.pack(side='left', fill='both', expand=True)
        wsb.pack(side='right', fill='y')

        self.week_tree.bind('<<TreeviewSelect>>', self._on_week_select)

        # ─── 右側：日誌明細（日期分組，每日全部內容一次顯示）───
        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        ttk.Label(right, text="日誌明細", font=FONT_BODY_BOLD).pack(
            anchor='w', padx=8, pady=(4, 2))

        # 用捲動式 Frame 顯示每日內容（不用 Treeview）
        detail_container = ttk.Frame(right)
        detail_container.pack(fill='both', expand=True)

        self.detail_canvas = tk.Canvas(detail_container, bg='white',
                                        highlightthickness=0)
        self.detail_vsb = ttk.Scrollbar(detail_container, orient='vertical',
                                          command=self.detail_canvas.yview)
        self.detail_canvas.configure(yscrollcommand=self.detail_vsb.set)

        self.detail_inner = ttk.Frame(self.detail_canvas)
        self.detail_canvas_win = self.detail_canvas.create_window(
            (0, 0), window=self.detail_inner, anchor='nw')

        self.detail_inner.bind('<Configure>',
            lambda e: self.detail_canvas.configure(
                scrollregion=self.detail_canvas.bbox('all')))
        self.detail_canvas.bind('<Configure>',
            lambda e: self.detail_canvas.itemconfigure(
                self.detail_canvas_win, width=e.width))
        self.detail_canvas.bind('<Enter>',
            lambda e: self.detail_canvas.bind_all(
                '<MouseWheel>', self._on_detail_wheel))
        self.detail_canvas.bind('<Leave>',
            lambda e: self.detail_canvas.unbind_all('<MouseWheel>'))

        self.detail_canvas.pack(side='left', fill='both', expand=True)
        self.detail_vsb.pack(side='right', fill='y')

        self.week_data = {}   # iid -> (week_start, logs)
        self.all_logs = []

    def _on_detail_wheel(self, event):
        self.detail_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    # ─── 資料刷新 ──────────────────────────────────────────

    def _refresh(self):
        self.all_logs = self.db.get_work_logs(self.task_id)

        # 計算總工時（以天為單位）
        total = sum(log.hours for log in self.all_logs)
        self.total_label.configure(text=f"{total:.1f} 天")

        # 按週分組
        weeks = defaultdict(list)
        for log in self.all_logs:
            try:
                d = datetime.strptime(log.log_date, '%Y-%m-%d').date()
                week_start = d - timedelta(days=d.weekday())
                weeks[week_start].append(log)
            except ValueError:
                weeks[date(1900, 1, 1)].append(log)

        # 更新左側週列表
        self.week_tree.delete(*self.week_tree.get_children())
        self.week_data.clear()

        for week_start in sorted(weeks.keys(), reverse=True):
            logs = weeks[week_start]
            week_end = week_start + timedelta(days=6)
            week_days = sum(l.hours for l in logs)

            if week_start == date(1900, 1, 1):
                label = '(其他)'
            else:
                label = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"

            iid = week_start.isoformat()
            self.week_tree.insert('', 'end', iid=iid,
                                  values=(label, f'{week_days:.1f}'))
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
        """顯示選定週的日誌：按日期分組，每日全部內容一次顯示"""
        # 清除舊內容
        for w in self.detail_inner.winfo_children():
            w.destroy()

        data = self.week_data.get(week_iid)
        if not data:
            return

        _, logs = data

        # 按日期分組
        by_date = defaultdict(list)
        for log in logs:
            by_date[log.log_date].append(log)

        for log_date in sorted(by_date.keys(), reverse=True):
            day_logs = by_date[log_date]
            day_total = sum(l.hours for l in day_logs)

            # 日期標頭（藍色背景）
            header = tk.Frame(self.detail_inner, bg='#E3F2FD')
            header.pack(fill='x', padx=4, pady=(6, 0))

            tk.Label(header, text=f"\u25CF {log_date}",
                     bg='#E3F2FD', fg='#1565C0',
                     font=(FONT_FAMILY, 10, 'bold'),
                     padx=8, pady=4).pack(side='left')
            tk.Label(header, text=f"{day_total:.1f} 天",
                     bg='#E3F2FD', fg='#555555',
                     font=(FONT_FAMILY, 9),
                     padx=8, pady=4).pack(side='right')

            # 每筆日誌的內容
            for log in day_logs:
                entry_frame = tk.Frame(self.detail_inner, bg='white',
                                        highlightthickness=1,
                                        highlightbackground='#E0E0E0')
                entry_frame.pack(fill='x', padx=4, pady=(2, 0))

                # 工時標記
                top_row = tk.Frame(entry_frame, bg='white')
                top_row.pack(fill='x', padx=8, pady=(4, 0))
                tk.Label(top_row, text=f"{log.hours:.1f} 天",
                         bg='white', fg='#888888',
                         font=(FONT_FAMILY, 8)).pack(side='left')

                # 編輯按鈕
                edit_btn = tk.Label(top_row, text='✏️', bg='white',
                                     fg='#1565C0', cursor='hand2',
                                     font=(FONT_FAMILY, 9))
                edit_btn.pack(side='right', padx=(4, 0))
                edit_btn.bind('<Button-1>',
                              lambda e, l=log: self._edit_log(l))

                # 刪除按鈕
                del_btn = tk.Label(top_row, text='\u2716', bg='white',
                                    fg='#CC0000', cursor='hand2',
                                    font=(FONT_FAMILY, 9))
                del_btn.pack(side='right')
                del_btn.bind('<Button-1>',
                             lambda e, lid=log.id: self._delete_log(lid))

                # 內容文字 — 支援可點擊超連結
                content_frame = tk.Frame(entry_frame, bg='white')
                content_frame.pack(fill='x', padx=8, pady=(2, 6))

                content_text = tk.Text(content_frame, height=1, wrap='word',
                                        bg='white', relief='flat',
                                        font=(FONT_FAMILY, 9),
                                        cursor='arrow')
                content_text.pack(fill='x')

                self._insert_with_links(content_text, log.content)

                # 自動調整高度
                content_text.configure(state='disabled')
                content_text.bind('<Configure>',
                    lambda e, t=content_text: self._auto_height(t))

                # 雙擊整個 entry 開啟編輯
                self._bind_double_click(entry_frame, log)

    def _insert_with_links(self, text_widget, content):
        """插入文字，將檔案路徑和 URL 轉為可點擊連結"""
        import re
        # 匹配 file:///path、http(s)://url、或 Windows 路徑 (C:\..., \\server\...)
        link_pattern = re.compile(
            r'(file:///[^\s]+|https?://[^\s]+|[A-Za-z]:\\[^\s,]+|\\\\[^\s,]+)')

        last_end = 0
        for match in link_pattern.finditer(content):
            # 普通文字
            if match.start() > last_end:
                text_widget.insert('end', content[last_end:match.start()])

            # 連結文字
            link = match.group(0)
            tag_name = f'link_{match.start()}'
            text_widget.insert('end', link, tag_name)
            text_widget.tag_configure(tag_name, foreground='#1565C0',
                                       underline=True)
            text_widget.tag_bind(tag_name, '<Button-1>',
                                  lambda e, path=link: self._open_link(path))
            text_widget.tag_bind(tag_name, '<Enter>',
                                  lambda e, t=text_widget: t.configure(
                                      cursor='hand2'))
            text_widget.tag_bind(tag_name, '<Leave>',
                                  lambda e, t=text_widget: t.configure(
                                      cursor='arrow'))
            last_end = match.end()

        # 剩餘文字
        if last_end < len(content):
            text_widget.insert('end', content[last_end:])

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
                # Windows 路徑
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("無法開啟", f"無法開啟：\n{path}\n\n{e}",
                                 parent=self.win)

    def _auto_height(self, text_widget):
        """自動調整 Text widget 高度"""
        text_widget.update_idletasks()
        line_count = int(text_widget.index('end-1c').split('.')[0])
        text_widget.configure(height=max(1, line_count))

    # ─── 新增日誌 ──────────────────────────────────────────

    def _add_log(self):
        _AddLogDialog(self.win, self.db, self.task_id,
                      on_save=self._refresh)

    # ─── 編輯日誌 ──────────────────────────────────────────

    def _bind_double_click(self, frame, log):
        """為 frame 及所有子元件綁定雙擊事件"""
        def on_dbl(e):
            self._edit_log(log)
        frame.bind('<Double-Button-1>', on_dbl)
        for child in frame.winfo_children():
            try:
                child.bind('<Double-Button-1>', on_dbl)
            except Exception:
                pass
            # 遞迴子層
            for sub in child.winfo_children():
                try:
                    sub.bind('<Double-Button-1>', on_dbl)
                except Exception:
                    pass

    def _edit_log(self, log):
        _EditLogDialog(self.win, self.db, log, on_save=self._refresh)

    # ─── 刪除日誌 ──────────────────────────────────────────

    def _delete_log(self, log_id):
        if messagebox.askyesno("確認刪除", "確定要刪除此日誌？",
                                parent=self.win):
            self.db.delete_work_log(log_id)
            self._refresh()


class _AddLogDialog:
    def __init__(self, parent, db, task_id, on_save=None):
        self.db = db
        self.task_id = task_id
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("新增工作日誌")
        self.win.geometry("500x420")
        self.win.resizable(True, True)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=16)
        f.pack(fill='both', expand=True)

        # 日期（用 DateEntry）
        ttk.Label(f, text="日期:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.date_var = tk.StringVar(value=date.today().isoformat())
        from ui.date_picker import DateEntry
        de = DateEntry(f, textvariable=self.date_var)
        de.pack(fill='x', pady=(0, 8))

        # 工時（天）
        ttk.Label(f, text="工時 (天):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.hours_var = tk.StringVar(value="1.0")
        ttk.Entry(f, textvariable=self.hours_var, font=FONT_BODY).pack(
            fill='x', pady=(0, 8))

        # 內容（加大）
        ttk.Label(f, text="內容 (支援檔案路徑連結，如 C:\\path\\file.doc):",
                  font=FONT_BODY_BOLD).pack(anchor='w')
        self.content_text = tk.Text(f, height=10, font=FONT_BODY, wrap='word')
        self.content_text.pack(fill='both', expand=True, pady=(0, 10))

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


class _EditLogDialog:
    """編輯既有工作日誌"""
    def __init__(self, parent, db, log, on_save=None):
        self.db = db
        self.log = log
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("編輯工作日誌")
        self.win.geometry("500x420")
        self.win.resizable(True, True)
        self.win.transient(parent)
        self.win.grab_set()

        f = ttk.Frame(self.win, padding=16)
        f.pack(fill='both', expand=True)

        # 日期
        ttk.Label(f, text="日期:", font=FONT_BODY_BOLD).pack(anchor='w')
        self.date_var = tk.StringVar(value=log.log_date)
        from ui.date_picker import DateEntry
        de = DateEntry(f, textvariable=self.date_var)
        de.pack(fill='x', pady=(0, 8))

        # 工時（天）
        ttk.Label(f, text="工時 (天):", font=FONT_BODY_BOLD).pack(anchor='w')
        self.hours_var = tk.StringVar(value=f"{log.hours:.1f}")
        ttk.Entry(f, textvariable=self.hours_var, font=FONT_BODY).pack(
            fill='x', pady=(0, 8))

        # 內容
        ttk.Label(f, text="內容 (支援檔案路徑連結，如 C:\\path\\file.doc):",
                  font=FONT_BODY_BOLD).pack(anchor='w')
        self.content_text = tk.Text(f, height=10, font=FONT_BODY, wrap='word')
        self.content_text.pack(fill='both', expand=True, pady=(0, 10))
        if log.content:
            self.content_text.insert('1.0', log.content)

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
        self.db.update_work_log(self.log.id, d, content, hours)
        if self.on_save:
            self.on_save()
        self.win.destroy()
