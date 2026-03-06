"""甘特圖視圖：OpenProject 風格 — 任務名稱顯示在條上 + 狀態色彩"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime, timedelta, date
from constants import (CHART_COLORS, FONT_FAMILY, FONT_BODY, FONT_BODY_BOLD,
                       STATUS_COLORS, PRIORITY_COLORS)

ROW_HEIGHT = 34
WEEK_WIDTH = 42
HEADER_HEIGHT = 50
LABEL_WIDTH = 200
MILESTONE_SIZE = 8

# 狀態對應條色（OpenProject 風格）
BAR_COLORS = {
    '待辦':   '#90CAF9',   # 淺藍
    '進行中': '#1565C0',   # 深藍
    '審核中': '#FB8C00',   # 橘
    '已完成': '#2E7D32',   # 綠
}


class _CanvasTooltip:
    """Canvas 上的浮動提示"""
    def __init__(self, canvas):
        self.canvas = canvas
        self.tip_window = None

    def show(self, x, y, text):
        self.hide()
        sx = self.canvas.winfo_rootx() + x
        sy = self.canvas.winfo_rooty() + y - 40

        self.tip_window = tw = tk.Toplevel(self.canvas)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{sx}+{sy}")

        frame = tk.Frame(tw, bg='#333333', padx=1, pady=1)
        frame.pack()
        label = tk.Label(frame, text=text, justify='left',
                         background='#333333', foreground='white',
                         font=(FONT_FAMILY, 9), padx=8, pady=4)
        label.pack()

    def hide(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class GanttView(ttk.Frame):
    def __init__(self, parent, on_task_click=None):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self.tasks = []
        self.milestones = []
        self.rows = []
        self.group_by = 'project'
        self.project_lookup = {}

        self._build_ui()
        self.tooltip = _CanvasTooltip(self.timeline_canvas)

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

        ttk.Button(ctrl, text="<< 今天", command=self._scroll_to_today,
                   style='Toolbar.TButton').pack(side='left')

        # 主區域
        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=4, pady=4)

        # 左側標籤 Canvas
        self.label_canvas = tk.Canvas(body, width=LABEL_WIDTH, bg='white',
                                       highlightthickness=0)
        self.label_canvas.pack(side='left', fill='y')

        # 分隔線
        tk.Frame(body, bg='#D0D0D0', width=1).pack(side='left', fill='y')

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
            self.rows.append((f"\u25B8 {group_name}", None, '#E8E8E8'))
            color = CHART_COLORS[color_idx % len(CHART_COLORS)]
            for t in sorted(groups[group_name],
                            key=lambda x: x.start_date or ''):
                self.rows.append((t.title, t, color))
            color_idx += 1

    def _get_date_range(self):
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
        self.tooltip.hide()

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

        self.label_canvas.configure(scrollregion=(0, 0, LABEL_WIDTH, canvas_h))
        self.timeline_canvas.configure(scrollregion=(0, 0, canvas_w, canvas_h))

        # ── 時間軸標頭 ──
        # 月份標頭（頂部）
        current = min_date.replace(day=1)
        while current < max_date:
            x = self._date_to_x(current, min_date)
            next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
            x2 = self._date_to_x(next_month, min_date)
            # 月份背景
            self.timeline_canvas.create_rectangle(
                x, 0, x2, 22, fill='#F5F5F5', outline='#E0E0E0')
            month_str = current.strftime('%Y / %m')
            self.timeline_canvas.create_text(
                (x + x2) // 2, 11, text=month_str,
                font=(FONT_FAMILY, 8, 'bold'), fill='#555555')
            current = next_month

        # 週日期
        for w in range(total_weeks):
            x = w * WEEK_WIDTH
            week_date = min_date + timedelta(weeks=w)
            self.timeline_canvas.create_text(
                x + WEEK_WIDTH // 2, 36, text=week_date.strftime('%m/%d'),
                font=(FONT_FAMILY, 7), fill='#999999')
            self.timeline_canvas.create_line(
                x, HEADER_HEIGHT, x, canvas_h, fill='#F0F0F0', width=1)

        self.timeline_canvas.create_line(
            0, HEADER_HEIGHT, canvas_w, HEADER_HEIGHT, fill='#D0D0D0')
        self.label_canvas.create_rectangle(
            0, 0, LABEL_WIDTH, HEADER_HEIGHT, fill='#F5F5F5', outline='')
        self.label_canvas.create_text(
            10, HEADER_HEIGHT // 2, text='任務', anchor='w',
            font=(FONT_FAMILY, 9, 'bold'), fill='#555555')
        self.label_canvas.create_line(
            0, HEADER_HEIGHT, LABEL_WIDTH, HEADER_HEIGHT, fill='#D0D0D0')

        # ── 繪製列 ──
        for i, (label, task, color) in enumerate(self.rows):
            y = HEADER_HEIGHT + i * ROW_HEIGHT
            is_group = task is None
            bg = '#F0F0F0' if is_group else ('#FAFAFA' if i % 2 == 0 else '#FFFFFF')

            self.label_canvas.create_rectangle(
                0, y, LABEL_WIDTH, y + ROW_HEIGHT, fill=bg, outline='')
            self.timeline_canvas.create_rectangle(
                0, y, canvas_w, y + ROW_HEIGHT, fill=bg, outline='')

            # 水平分隔線
            self.label_canvas.create_line(
                0, y + ROW_HEIGHT, LABEL_WIDTH, y + ROW_HEIGHT,
                fill='#EEEEEE', width=1)
            self.timeline_canvas.create_line(
                0, y + ROW_HEIGHT, canvas_w, y + ROW_HEIGHT,
                fill='#EEEEEE', width=1)

            if is_group:
                # 群組標題
                self.label_canvas.create_text(
                    10, y + ROW_HEIGHT // 2, text=label, anchor='w',
                    font=(FONT_FAMILY, 10, 'bold'), fill='#333333')
            else:
                # 任務名稱（左側有狀態小色點）
                status_color = STATUS_COLORS.get(task.status, '#999999')
                self.label_canvas.create_oval(
                    10, y + ROW_HEIGHT // 2 - 4,
                    18, y + ROW_HEIGHT // 2 + 4,
                    fill=status_color, outline='')

                display = label[:18] + '..' if len(label) > 19 else label
                self.label_canvas.create_text(
                    24, y + ROW_HEIGHT // 2, text=display, anchor='w',
                    font=(FONT_FAMILY, 9), fill='#333333')

            if task and task.start_date and task.estimated_weeks:
                try:
                    sd = datetime.strptime(task.start_date, '%Y-%m-%d').date()
                    ed = sd + timedelta(weeks=task.estimated_weeks)
                    x1 = self._date_to_x(sd, min_date)
                    x2 = self._date_to_x(ed, min_date)

                    bar_color = BAR_COLORS.get(task.status, color)

                    # 圓角矩形效果（用兩個矩形+圓圈模擬）
                    bar_y1 = y + 7
                    bar_y2 = y + ROW_HEIGHT - 7
                    bar_x2 = max(x1 + 8, x2)

                    bar_id = self.timeline_canvas.create_rectangle(
                        x1, bar_y1, bar_x2, bar_y2,
                        fill=bar_color, outline='', width=0)

                    # 任務名稱顯示在條右側（OpenProject 風格）
                    bar_w = bar_x2 - x1
                    name_text = task.title
                    if bar_w > 60:
                        # 條夠寬：名稱放在條內
                        max_chars = bar_w // 8
                        disp = name_text[:max_chars]
                        if len(name_text) > max_chars:
                            disp = disp[:-2] + '..'
                        name_id = self.timeline_canvas.create_text(
                            x1 + 6, (bar_y1 + bar_y2) // 2,
                            text=disp, anchor='w',
                            font=(FONT_FAMILY, 8, 'bold'), fill='white')
                        self._bind_bar_events(name_id, task.id,
                                              self._bar_tip(task, ed))
                    else:
                        # 條太窄：名稱放在條右側
                        disp = name_text[:16]
                        if len(name_text) > 16:
                            disp = disp[:-2] + '..'
                        self.timeline_canvas.create_text(
                            bar_x2 + 4, (bar_y1 + bar_y2) // 2,
                            text=disp, anchor='w',
                            font=(FONT_FAMILY, 8), fill='#555555')

                    self._bind_bar_events(bar_id, task.id,
                                          self._bar_tip(task, ed))
                except ValueError:
                    pass

        # ── 里程碑 ──
        for ms in self.milestones:
            try:
                md = datetime.strptime(ms.target_date, '%Y-%m-%d').date()
                mx = self._date_to_x(md, min_date)

                # 虛線（整個高度）
                self.timeline_canvas.create_line(
                    mx, HEADER_HEIGHT, mx, canvas_h,
                    fill='#E15759', width=1, dash=(4, 4))

                # 菱形圖示
                my_top = HEADER_HEIGHT + 2
                diamond = self.timeline_canvas.create_polygon(
                    mx, my_top,
                    mx + MILESTONE_SIZE, my_top + MILESTONE_SIZE,
                    mx, my_top + MILESTONE_SIZE * 2,
                    mx - MILESTONE_SIZE, my_top + MILESTONE_SIZE,
                    fill='#E15759', outline='#C0392B', width=1)

                # 名稱標籤
                name_id = self.timeline_canvas.create_text(
                    mx + MILESTONE_SIZE + 4, my_top + MILESTONE_SIZE,
                    text=ms.name, anchor='w',
                    font=(FONT_FAMILY, 8, 'bold'), fill='#C0392B')

                tip_text = (f"\u25C6 {ms.name}\n"
                            f"日期: {ms.target_date}")
                if ms.description:
                    tip_text += f"\n{ms.description}"

                self._bind_milestone_tooltip(diamond, tip_text)
                self._bind_milestone_tooltip(name_id, tip_text)
            except ValueError:
                pass

        # ── 今天紅線 ──
        today_x = self._date_to_x(today, min_date)
        self.timeline_canvas.create_line(
            today_x, 0, today_x, canvas_h,
            fill='#DC3545', width=2, dash=(6, 3))
        # 「Today」標記
        self.timeline_canvas.create_rectangle(
            today_x - 22, 2, today_x + 22, 18,
            fill='#DC3545', outline='')
        self.timeline_canvas.create_text(
            today_x, 10, text='Today',
            font=(FONT_FAMILY, 7, 'bold'), fill='white')

    def _bar_tip(self, task, end_date):
        """產生任務條 tooltip 文字"""
        lines = [task.title]
        lines.append(f"{task.start_date} ~ {end_date.isoformat()}")
        lines.append(f"{task.estimated_weeks} 週 | {task.status}")
        if task.assignee:
            lines.append(f"負責人: {task.assignee}")
        return '\n'.join(lines)

    def _bind_bar_events(self, item_id, task_id, tip_text):
        def _enter(e):
            self.timeline_canvas.configure(cursor='hand2')
            self.tooltip.show(e.x, e.y, tip_text)

        def _leave(e):
            self.timeline_canvas.configure(cursor='')
            self.tooltip.hide()

        def _click(e):
            self.tooltip.hide()
            if self.on_task_click:
                self.on_task_click(task_id)

        self.timeline_canvas.tag_bind(item_id, '<Enter>', _enter)
        self.timeline_canvas.tag_bind(item_id, '<Leave>', _leave)
        self.timeline_canvas.tag_bind(item_id, '<Button-1>', _click)

    def _bind_milestone_tooltip(self, item_id, tip_text):
        def _enter(e):
            self.timeline_canvas.configure(cursor='hand2')
            self.tooltip.show(e.x, e.y, tip_text)

        def _leave(e):
            self.timeline_canvas.configure(cursor='')
            self.tooltip.hide()

        self.timeline_canvas.tag_bind(item_id, '<Enter>', _enter)
        self.timeline_canvas.tag_bind(item_id, '<Leave>', _leave)

    def _scroll_to_today(self):
        min_date, max_date = self._get_date_range()
        total_weeks = max(1, (max_date - min_date).days // 7 + 1)
        canvas_w = total_weeks * WEEK_WIDTH
        if canvas_w <= 0:
            return
        today_x = self._date_to_x(date.today(), min_date)
        fraction = max(0, (today_x - 200) / canvas_w)
        self.timeline_canvas.xview_moveto(fraction)
