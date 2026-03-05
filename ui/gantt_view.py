"""甘特圖視圖：雙 Canvas 繪製（固定標籤 + 可捲動時間軸）"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime, timedelta, date
from constants import (CHART_COLORS, FONT_FAMILY, FONT_BODY, FONT_BODY_BOLD,
                       STATUS_COLORS)

ROW_HEIGHT = 32
WEEK_WIDTH = 40
HEADER_HEIGHT = 50
LABEL_WIDTH = 180
MILESTONE_SIZE = 8


class GanttView(ttk.Frame):
    def __init__(self, parent, on_task_click=None):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self.tasks = []
        self.milestones = []
        self.rows = []          # [(label, task_or_None, color), ...]
        self.group_by = 'project'
        self.project_lookup = {}

        self._build_ui()

    def _build_ui(self):
        # 頂部控制列
        ctrl = ttk.Frame(self)
        ctrl.pack(fill='x', padx=4, pady=(4, 0))

        ttk.Label(ctrl, text="分組:", font=FONT_BODY).pack(side='left')
        self.group_var = tk.StringVar(value='project')
        cb = ttk.Combobox(ctrl, textvariable=self.group_var,
                          values=['project', 'assignee'],
                          state='readonly', width=12, font=FONT_BODY)
        cb.pack(side='left', padx=(4, 12))
        cb.bind('<<ComboboxSelected>>', lambda e: self._rebuild())

        ttk.Button(ctrl, text="← 今天", command=self._scroll_to_today,
                   style='Toolbar.TButton').pack(side='left')

        # 主區域
        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=4, pady=4)

        # 左側標籤 Canvas
        self.label_canvas = tk.Canvas(body, width=LABEL_WIDTH, bg='white',
                                       highlightthickness=0)
        self.label_canvas.pack(side='left', fill='y')

        # 右側時間軸 Canvas + 水平捲軸
        right = ttk.Frame(body)
        right.pack(side='left', fill='both', expand=True)

        self.timeline_canvas = tk.Canvas(right, bg='white',
                                          highlightthickness=0)
        self.h_scroll = ttk.Scrollbar(right, orient='horizontal',
                                       command=self.timeline_canvas.xview)
        self.v_scroll = ttk.Scrollbar(body, orient='vertical',
                                       command=self._yview_both)
        self.timeline_canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set)
        self.label_canvas.configure(yscrollcommand=self.v_scroll.set)

        self.timeline_canvas.pack(fill='both', expand=True)
        self.h_scroll.pack(fill='x')
        self.v_scroll.pack(side='right', fill='y')

        # 滑鼠滾輪
        for c in (self.label_canvas, self.timeline_canvas):
            c.bind('<Enter>', lambda e, cv=c: cv.bind_all(
                '<MouseWheel>', self._on_mousewheel))
            c.bind('<Leave>', lambda e, cv=c: cv.unbind_all('<MouseWheel>'))

    def _yview_both(self, *args):
        self.label_canvas.yview(*args)
        self.timeline_canvas.yview(*args)

    def _on_mousewheel(self, event):
        self.label_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.timeline_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    # ─── 資料更新 ──────────────────────────────────────────

    def refresh(self, tasks, milestones=None, project_lookup=None):
        self.tasks = tasks
        self.milestones = milestones or []
        self.project_lookup = project_lookup or {}
        self._rebuild()

    def _rebuild(self):
        self.group_by = self.group_var.get()
        self._compute_rows()
        self._draw()

    def _compute_rows(self):
        self.rows = []
        # 只顯示有 start_date 且 estimated_weeks 的任務
        valid = [t for t in self.tasks
                 if t.start_date and t.estimated_weeks]

        if self.group_by == 'project':
            groups = {}
            for t in valid:
                key = self.project_lookup.get(t.project_id, f'專案{t.project_id}')
                groups.setdefault(key, []).append(t)
        else:
            groups = {}
            for t in valid:
                key = t.assignee or '未指派'
                groups.setdefault(key, []).append(t)

        color_idx = 0
        for group_name in sorted(groups.keys()):
            # 群組標題列
            self.rows.append((f"▸ {group_name}", None, '#E0E0E0'))
            color = CHART_COLORS[color_idx % len(CHART_COLORS)]
            for t in groups[group_name]:
                self.rows.append((t.title, t, color))
            color_idx += 1

    def _get_date_range(self):
        """計算時間軸起訖日"""
        dates = []
        for t in self.tasks:
            if t.start_date:
                try:
                    d = datetime.strptime(t.start_date, '%Y-%m-%d').date()
                    dates.append(d)
                    if t.estimated_weeks:
                        dates.append(d + timedelta(weeks=t.estimated_weeks))
                except ValueError:
                    pass
        for ms in self.milestones:
            try:
                dates.append(datetime.strptime(ms.target_date, '%Y-%m-%d').date())
            except ValueError:
                pass

        if not dates:
            today = date.today()
            return today - timedelta(weeks=2), today + timedelta(weeks=12)

        min_d = min(dates) - timedelta(weeks=2)
        max_d = max(dates) + timedelta(weeks=4)
        return min_d, max_d

    def _date_to_x(self, d, origin):
        delta = (d - origin).days
        return int(delta / 7 * WEEK_WIDTH)

    def _draw(self):
        self.label_canvas.delete('all')
        self.timeline_canvas.delete('all')

        if not self.rows:
            self.timeline_canvas.create_text(
                200, 80, text="尚無甘特圖資料\n請為任務設定「開始日期」和「預估週數」",
                font=(FONT_FAMILY, 11), fill='#999999', justify='center')
            return

        min_date, max_date = self._get_date_range()
        total_weeks = max(1, (max_date - min_date).days // 7 + 1)
        canvas_w = total_weeks * WEEK_WIDTH
        canvas_h = HEADER_HEIGHT + len(self.rows) * ROW_HEIGHT + 20
        today = date.today()

        # 設定捲動區域
        self.label_canvas.configure(scrollregion=(0, 0, LABEL_WIDTH, canvas_h))
        self.timeline_canvas.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        # ── 繪製時間軸標頭 ──
        # 月份標頭
        current = min_date
        while current < max_date:
            x = self._date_to_x(current, min_date)
            month_str = current.strftime('%Y/%m')
            self.timeline_canvas.create_text(
                x + 4, 10, text=month_str, anchor='nw',
                font=(FONT_FAMILY, 8, 'bold'), fill='#333333')
            # 跳到下個月
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)

        # 週刻度
        for w in range(total_weeks):
            x = w * WEEK_WIDTH
            week_date = min_date + timedelta(weeks=w)
            # 週一日期
            self.timeline_canvas.create_text(
                x + 2, 28, text=week_date.strftime('%m/%d'), anchor='nw',
                font=(FONT_FAMILY, 7), fill='#888888')
            # 垂直格線
            self.timeline_canvas.create_line(
                x, HEADER_HEIGHT, x, canvas_h, fill='#E8E8E8', width=1)

        # 分隔線
        self.timeline_canvas.create_line(
            0, HEADER_HEIGHT, canvas_w, HEADER_HEIGHT, fill='#CCCCCC')
        self.label_canvas.create_line(
            0, HEADER_HEIGHT, LABEL_WIDTH, HEADER_HEIGHT, fill='#CCCCCC')

        # ── 繪製列 ──
        for i, (label, task, color) in enumerate(self.rows):
            y = HEADER_HEIGHT + i * ROW_HEIGHT

            # 交替背景
            if i % 2 == 0:
                bg = '#FAFAFA'
            else:
                bg = '#FFFFFF'

            if task is None:
                bg = '#F0F0F0'

            self.label_canvas.create_rectangle(
                0, y, LABEL_WIDTH, y + ROW_HEIGHT, fill=bg, outline='')
            self.timeline_canvas.create_rectangle(
                0, y, canvas_w, y + ROW_HEIGHT, fill=bg, outline='')

            # 標籤文字
            display = label[:14] + '…' if len(label) > 15 else label
            font = (FONT_FAMILY, 9, 'bold') if task is None else (FONT_FAMILY, 9)
            self.label_canvas.create_text(
                8, y + ROW_HEIGHT // 2, text=display, anchor='w',
                font=font, fill='#333333')

            # 任務長條
            if task and task.start_date and task.estimated_weeks:
                try:
                    sd = datetime.strptime(task.start_date, '%Y-%m-%d').date()
                    ed = sd + timedelta(weeks=task.estimated_weeks)
                    x1 = self._date_to_x(sd, min_date)
                    x2 = self._date_to_x(ed, min_date)

                    # 根據狀態調整透明度
                    bar_color = color
                    if task.status == '已完成':
                        bar_color = '#198754'

                    bar_id = self.timeline_canvas.create_rectangle(
                        x1, y + 6, max(x1 + 4, x2), y + ROW_HEIGHT - 6,
                        fill=bar_color, outline='', tags=('task_bar',))

                    # 在長條上顯示週數
                    bar_w = x2 - x1
                    if bar_w > 30:
                        self.timeline_canvas.create_text(
                            (x1 + x2) // 2, y + ROW_HEIGHT // 2,
                            text=f"{task.estimated_weeks}w",
                            font=(FONT_FAMILY, 7, 'bold'), fill='white',
                            tags=('task_bar',))

                    # 點擊事件
                    if self.on_task_click:
                        self.timeline_canvas.tag_bind(
                            bar_id, '<Button-1>',
                            lambda e, tid=task.id: self.on_task_click(tid))
                        self.timeline_canvas.tag_bind(
                            bar_id, '<Enter>',
                            lambda e: self.timeline_canvas.configure(cursor='hand2'))
                        self.timeline_canvas.tag_bind(
                            bar_id, '<Leave>',
                            lambda e: self.timeline_canvas.configure(cursor=''))
                except ValueError:
                    pass

        # ── 里程碑 ──
        for ms in self.milestones:
            try:
                md = datetime.strptime(ms.target_date, '%Y-%m-%d').date()
                mx = self._date_to_x(md, min_date)
                my_top = HEADER_HEIGHT + 2

                # 菱形
                self.timeline_canvas.create_polygon(
                    mx, my_top,
                    mx + MILESTONE_SIZE, my_top + MILESTONE_SIZE,
                    mx, my_top + MILESTONE_SIZE * 2,
                    mx - MILESTONE_SIZE, my_top + MILESTONE_SIZE,
                    fill='#E15759', outline='#C0392B', width=1,
                    tags=('milestone',))

                # 虛線貫穿
                self.timeline_canvas.create_line(
                    mx, HEADER_HEIGHT, mx, canvas_h,
                    fill='#E15759', width=1, dash=(4, 4),
                    tags=('milestone',))

                # 標籤
                self.timeline_canvas.create_text(
                    mx + MILESTONE_SIZE + 2, my_top + MILESTONE_SIZE,
                    text=ms.name, anchor='w',
                    font=(FONT_FAMILY, 7, 'bold'), fill='#E15759',
                    tags=('milestone',))
            except ValueError:
                pass

        # ── 今天紅線 ──
        today_x = self._date_to_x(today, min_date)
        self.timeline_canvas.create_line(
            today_x, 0, today_x, canvas_h,
            fill='#DC3545', width=2, dash=(6, 3), tags=('today',))
        self.timeline_canvas.create_text(
            today_x, 4, text='Today', anchor='n',
            font=(FONT_FAMILY, 7, 'bold'), fill='#DC3545', tags=('today',))

    def _scroll_to_today(self):
        """捲動到今天的位置"""
        min_date, max_date = self._get_date_range()
        total_weeks = max(1, (max_date - min_date).days // 7 + 1)
        canvas_w = total_weeks * WEEK_WIDTH
        if canvas_w <= 0:
            return
        today_x = self._date_to_x(date.today(), min_date)
        fraction = max(0, (today_x - 200) / canvas_w)
        self.timeline_canvas.xview_moveto(fraction)
