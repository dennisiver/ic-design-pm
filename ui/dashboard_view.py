"""儀表板視圖：OpenProject 風格 — 數字摘要卡 + 圖表 + 到期清單 + 專案進度"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import date, datetime, timedelta
from constants import (FONT_FAMILY, FONT_BODY, FONT_BODY_BOLD, FONT_TITLE,
                       CHART_COLORS, STATUS_COLORS)
from ui.chart_utils import draw_donut_chart, draw_bar_chart


class DashboardView(ttk.Frame):
    def __init__(self, parent, on_task_click=None):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self._build_ui()

    def _build_ui(self):
        # 主捲動區域
        self.canvas = tk.Canvas(self, bg='#F0F2F5', highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        self.inner = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor='nw')

        self.canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.inner.bind('<Configure>',
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.canvas.bind('<Enter>', self._bind_mw)
        self.canvas.bind('<Leave>', self._unbind_mw)

        # ── Row 1: 數字摘要卡 ──
        self.summary_frame = ttk.Frame(self.inner)
        self.summary_frame.pack(fill='x', padx=16, pady=(16, 8))

        self.card_data = [
            ('total',       '總任務',    '0', '#1565C0', '\U0001F4CB'),
            ('overdue',     '逾期任務',  '0', '#C62828', '\u26A0\uFE0F'),
            ('this_week',   '本週到期',  '0', '#E65100', '\U0001F4C5'),
            ('in_progress', '進行中',    '0', '#2E7D32', '\u25B6\uFE0F'),
        ]
        self.summary_cards = {}
        for i, (key, title, val, color, icon) in enumerate(self.card_data):
            card = self._make_summary_card(self.summary_frame, title, val,
                                            color, icon)
            card.grid(row=0, column=i, sticky='nsew', padx=6, pady=4)
            self.summary_frame.columnconfigure(i, weight=1)
            self.summary_cards[key] = card

        # ── Row 2: 圖表列 ──
        chart_row1 = ttk.Frame(self.inner)
        chart_row1.pack(fill='x', padx=16, pady=6)

        self.status_canvas = tk.Canvas(chart_row1, width=240, height=260,
                                        bg='white', highlightthickness=1,
                                        highlightbackground='#E0E0E0')
        self.status_canvas.pack(side='left', padx=6, pady=4, expand=True)

        self.priority_canvas = tk.Canvas(chart_row1, width=240, height=260,
                                          bg='white', highlightthickness=1,
                                          highlightbackground='#E0E0E0')
        self.priority_canvas.pack(side='left', padx=6, pady=4, expand=True)

        self.assignee_canvas = tk.Canvas(chart_row1, width=240, height=260,
                                          bg='white', highlightthickness=1,
                                          highlightbackground='#E0E0E0')
        self.assignee_canvas.pack(side='left', padx=6, pady=4, expand=True)

        # ── Row 3: 類別 + 即將到期 ──
        chart_row2 = ttk.Frame(self.inner)
        chart_row2.pack(fill='x', padx=16, pady=6)

        self.category_canvas = tk.Canvas(chart_row2, width=300, height=260,
                                          bg='white', highlightthickness=1,
                                          highlightbackground='#E0E0E0')
        self.category_canvas.pack(side='left', padx=6, pady=4, expand=True)

        # 即將到期清單（白底卡片風格）
        upcoming_outer = tk.Frame(chart_row2, bg='white',
                                   highlightthickness=1,
                                   highlightbackground='#E0E0E0')
        upcoming_outer.pack(side='left', fill='both', padx=6, pady=4,
                            expand=True)

        tk.Label(upcoming_outer, text='\u23F0 即將到期 (7天內)',
                 bg='white', fg='#333333',
                 font=(FONT_FAMILY, 10, 'bold'),
                 anchor='w', padx=8, pady=6).pack(fill='x')
        tk.Frame(upcoming_outer, bg='#E0E0E0', height=1).pack(fill='x')

        cols = ('title', 'due', 'status')
        self.upcoming_tree = ttk.Treeview(upcoming_outer, columns=cols,
                                           show='headings', height=8)
        self.upcoming_tree.heading('title', text='任務')
        self.upcoming_tree.heading('due', text='到期日')
        self.upcoming_tree.heading('status', text='狀態')
        self.upcoming_tree.column('title', width=160, minwidth=80)
        self.upcoming_tree.column('due', width=90, minwidth=70)
        self.upcoming_tree.column('status', width=70, minwidth=50)
        self.upcoming_tree.pack(fill='both', expand=True, padx=4, pady=4)
        self.upcoming_tree.bind('<Double-1>', self._on_upcoming_click)
        self.upcoming_map = {}

        # ── Row 4: 各專案進度 ──
        progress_outer = tk.Frame(self.inner, bg='white',
                                   highlightthickness=1,
                                   highlightbackground='#E0E0E0')
        progress_outer.pack(fill='x', padx=16, pady=(6, 16))

        tk.Label(progress_outer, text='\U0001F4CA 各專案進度',
                 bg='white', fg='#333333',
                 font=(FONT_FAMILY, 10, 'bold'),
                 anchor='w', padx=8, pady=6).pack(fill='x')
        tk.Frame(progress_outer, bg='#E0E0E0', height=1).pack(fill='x')

        self.progress_frame = tk.Frame(progress_outer, bg='white', padx=8,
                                        pady=8)
        self.progress_frame.pack(fill='x')

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _bind_mw(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mw)

    def _unbind_mw(self, event):
        self.canvas.unbind_all('<MouseWheel>')

    def _on_mw(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _make_summary_card(self, parent, title, value, color, icon=''):
        """OpenProject 風格：白底卡片 + 左側彩色邊條"""
        card = tk.Frame(parent, bg='white',
                        highlightthickness=1,
                        highlightbackground='#E0E0E0')

        # 左側色條
        bar = tk.Frame(card, bg=color, width=4)
        bar.pack(side='left', fill='y')

        inner = tk.Frame(card, bg='white', padx=14, pady=10)
        inner.pack(side='left', fill='both', expand=True)

        # 標題行 (icon + text)
        tk.Label(inner, text=f"{icon} {title}", bg='white',
                 font=(FONT_FAMILY, 9), fg='#888888').pack(anchor='w')
        lbl = tk.Label(inner, text=value, bg='white',
                       font=(FONT_FAMILY, 24, 'bold'), fg=color)
        lbl.pack(anchor='w', pady=(2, 0))
        card._value_label = lbl
        card._color = color
        return card

    def _update_card(self, key, value):
        card = self.summary_cards.get(key)
        if card:
            card._value_label.configure(text=str(value))

    # ─── 資料更新 ──────────────────────────────────────────

    def refresh(self, tasks, stats=None, milestones=None,
                project_progress=None):
        today = date.today()
        week_later = today + timedelta(days=7)

        total = len(tasks)
        overdue = 0
        this_week = 0
        in_progress = 0

        for t in tasks:
            if t.status == '進行中':
                in_progress += 1
            if t.due_date and t.status != '已完成':
                try:
                    dd = datetime.strptime(t.due_date, '%Y-%m-%d').date()
                    if dd < today:
                        overdue += 1
                    elif dd <= week_later:
                        this_week += 1
                except ValueError:
                    pass

        self._update_card('total', total)
        self._update_card('overdue', overdue)
        self._update_card('this_week', this_week)
        self._update_card('in_progress', in_progress)

        # 圖表
        if stats:
            draw_donut_chart(self.status_canvas,
                             stats.get('by_status', []),
                             120, 130, 80, title='狀態分布')
            draw_bar_chart(self.priority_canvas,
                           stats.get('by_priority', []),
                           0, 0, 240, 260, title='依優先級', horizontal=True)
            draw_bar_chart(self.assignee_canvas,
                           stats.get('by_assignee', []),
                           0, 0, 240, 260, title='依負責人', horizontal=True)
            draw_bar_chart(self.category_canvas,
                           stats.get('by_category', []),
                           0, 0, 300, 260, title='依類別', horizontal=True)

        # 即將到期清單
        self.upcoming_tree.delete(*self.upcoming_tree.get_children())
        self.upcoming_map.clear()
        upcoming = []
        for t in tasks:
            if t.due_date and t.status != '已完成':
                try:
                    dd = datetime.strptime(t.due_date, '%Y-%m-%d').date()
                    if dd <= week_later:
                        upcoming.append((dd, t))
                except ValueError:
                    pass
        upcoming.sort(key=lambda x: x[0])

        for dd, t in upcoming:
            iid = str(t.id)
            tag = 'overdue' if dd < today else 'upcoming'
            self.upcoming_tree.insert('', 'end', iid=iid,
                                      values=(t.title[:24], t.due_date,
                                              t.status),
                                      tags=(tag,))
            self.upcoming_map[iid] = t

        self.upcoming_tree.tag_configure('overdue', foreground='#C62828')
        self.upcoming_tree.tag_configure('upcoming', foreground='#E65100')

        # 各專案進度
        self._draw_project_progress(project_progress)

    def _draw_project_progress(self, project_progress):
        for w in self.progress_frame.winfo_children():
            w.destroy()

        if not project_progress:
            tk.Label(self.progress_frame, text="無專案資料", bg='white',
                     font=(FONT_FAMILY, 9), fg='#999999').pack(anchor='w')
            return

        for i, pp in enumerate(project_progress):
            name = pp['name']
            total = pp['total']
            done = pp['done']
            in_prog = pp['in_progress']
            pct = (done / total * 100) if total > 0 else 0

            row = tk.Frame(self.progress_frame, bg='white')
            row.pack(fill='x', pady=4)

            # 專案名稱
            tk.Label(row, text=name, font=(FONT_FAMILY, 9, 'bold'),
                     bg='white', width=16, anchor='w').pack(side='left')

            # 進度條 Canvas（圓角風格）
            bar_canvas = tk.Canvas(row, height=18, bg='white',
                                    highlightthickness=0)
            bar_canvas.pack(side='left', fill='x', expand=True, padx=(4, 8))

            bar_canvas._data = (total, done, in_prog)
            bar_canvas.bind('<Configure>',
                            lambda e, c=bar_canvas: self._draw_progress_bar(c))

            # 比例文字
            tk.Label(row, text=f"{done}/{total}  ({pct:.0f}%)",
                     bg='white',
                     font=(FONT_FAMILY, 9), fg='#555555',
                     width=14, anchor='w').pack(side='left')

    def _draw_progress_bar(self, canvas):
        canvas.delete('all')
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        total, done, in_prog = canvas._data

        # 圓角背景
        r = h // 2
        canvas.create_rectangle(r, 0, w - r, h, fill='#E8E8E8', outline='')
        canvas.create_oval(0, 0, h, h, fill='#E8E8E8', outline='')
        canvas.create_oval(w - h, 0, w, h, fill='#E8E8E8', outline='')

        if total == 0:
            canvas.create_text(w // 2, h // 2, text='(無任務)',
                               font=(FONT_FAMILY, 7), fill='#999999')
            return

        # 已完成（綠）
        done_w = int(w * done / total)
        if done_w > h:
            canvas.create_rectangle(r, 0, done_w - r, h,
                                     fill='#2E7D32', outline='')
            canvas.create_oval(0, 0, h, h, fill='#2E7D32', outline='')
            canvas.create_oval(done_w - h, 0, done_w, h,
                               fill='#2E7D32', outline='')
        elif done_w > 0:
            canvas.create_oval(0, 0, h, h, fill='#2E7D32', outline='')

        # 進行中（藍）
        prog_w = int(w * in_prog / total)
        if prog_w > 0:
            canvas.create_rectangle(done_w, 0, done_w + prog_w, h,
                                     fill='#1565C0', outline='')

    def _on_upcoming_click(self, event):
        item = self.upcoming_tree.identify_row(event.y)
        if item and item in self.upcoming_map and self.on_task_click:
            self.on_task_click(self.upcoming_map[item].id)
