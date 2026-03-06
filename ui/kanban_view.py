"""看板視圖：OpenProject 風格四欄看板 + 拖拉支援"""

import tkinter as tk
import tkinter.ttk as ttk
from constants import (STATUSES, STATUS_COLORS, PRIORITY_COLORS,
                       CATEGORY_BADGE_COLORS, AVATAR_COLORS,
                       FONT_BODY_BOLD, FONT_SMALL, FONT_FAMILY)
from ui.drag_manager import DragManager

# 快取負責人 → 顏色對應
_assignee_color_cache = {}


def _get_avatar_color(name):
    if not name:
        return '#AAAAAA'
    if name not in _assignee_color_cache:
        idx = len(_assignee_color_cache) % len(AVATAR_COLORS)
        _assignee_color_cache[name] = AVATAR_COLORS[idx]
    return _assignee_color_cache[name]


class KanbanView(ttk.Frame):
    def __init__(self, parent, on_task_click, on_status_change, on_task_delete):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self.on_status_change = on_status_change
        self.on_task_delete = on_task_delete

        self.columns = {}
        self.drag_mgr = DragManager(self)
        self._build_columns()

    def _build_columns(self):
        for i, status in enumerate(STATUSES):
            self.columnconfigure(i, weight=1, uniform="kanban_col")
            col = ScrollableColumn(self, status, STATUS_COLORS[status])
            col.grid(row=0, column=i, sticky='nsew', padx=2, pady=2)
            self.columns[status] = col
        self.rowconfigure(0, weight=1)

    def refresh(self, tasks):
        grouped = {s: [] for s in STATUSES}
        for task in tasks:
            if task.status in grouped:
                grouped[task.status].append(task)

        for status, col in self.columns.items():
            col.clear()
            col.set_count(len(grouped[status]))
            for task in grouped[status]:
                card = self._create_card(col.inner_frame, task)
                card.pack(fill='x', padx=6, pady=3)
            col.update_scroll_region()

    # ─── OpenProject 風格卡片 ─────────────────────────────

    def _create_card(self, parent, task):
        card_bg = '#FFFFFF'
        hover_bg = '#F0F4FF'
        priority_color = PRIORITY_COLORS.get(task.priority, '#6C757D')

        # 外層卡片：白底 + 左側優先級色條
        card = tk.Frame(parent, bg=card_bg, cursor='hand2',
                        highlightthickness=1, highlightbackground='#E0E0E0')
        card._normal_bg = card_bg
        card._hover_bg = hover_bg
        card._skip_bg = set()  # 不需要遞迴變色的子元件

        # 左側色條（模擬 border-left）
        color_bar = tk.Frame(card, bg=priority_color, width=4)
        color_bar.pack(side='left', fill='y')
        card._skip_bg.add(id(color_bar))

        # 右側內容
        content = tk.Frame(card, bg=card_bg, padx=8, pady=6)
        content.pack(side='left', fill='both', expand=True)

        # Row 1：類別徽章
        if task.category:
            badge_frame = tk.Frame(content, bg=card_bg)
            badge_frame.pack(fill='x', pady=(0, 4))
            self._create_badge(badge_frame, task.category, card_bg)

        # Row 2：標題
        title_label = tk.Label(content, text=task.title, bg=card_bg,
                               font=(FONT_FAMILY, 10, 'bold'), anchor='w',
                               wraplength=190, justify='left', fg='#1A1A2E')
        title_label.pack(fill='x')

        # Row 3：到期日 + 預估週數
        meta_parts = []
        if task.due_date:
            meta_parts.append(task.due_date)
        if task.estimated_weeks:
            meta_parts.append(f"{task.estimated_weeks}w")
        if meta_parts:
            meta_label = tk.Label(content, text="  \u00b7  ".join(meta_parts),
                                  bg=card_bg, font=(FONT_FAMILY, 8),
                                  fg='#888888', anchor='w')
            meta_label.pack(fill='x', pady=(2, 0))

        # Row 4：底部列（優先級點 + 負責人頭像）
        bottom = tk.Frame(content, bg=card_bg)
        bottom.pack(fill='x', pady=(6, 0))

        # 優先級小圓點 + 文字
        pri_frame = tk.Frame(bottom, bg=card_bg)
        pri_frame.pack(side='left')
        dot = tk.Canvas(pri_frame, width=10, height=10, bg=card_bg,
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=priority_color, outline='')
        dot.pack(side='left', padx=(0, 3))
        card._skip_bg.add(id(dot))
        tk.Label(pri_frame, text=task.priority, bg=card_bg,
                 font=(FONT_FAMILY, 8), fg=priority_color).pack(side='left')

        # 負責人頭像（圓圈+首字母）
        if task.assignee:
            avatar = self._create_avatar(bottom, task.assignee, size=24)
            avatar.pack(side='right')
            card._skip_bg.add(id(avatar))

        # 事件綁定
        self._bind_hover(card, task)
        self.drag_mgr.bind_card(card, task)
        self._bind_right_click(card, task)

        return card

    def _create_badge(self, parent, category, parent_bg):
        """建立類別徽章（小圓角標籤）"""
        colors = CATEGORY_BADGE_COLORS.get(category, ('#555555', '#F0F0F0'))
        fg, bg = colors

        badge = tk.Label(parent, text=category, bg=bg, fg=fg,
                         font=(FONT_FAMILY, 7, 'bold'),
                         padx=6, pady=1, relief='flat',
                         highlightthickness=1, highlightbackground=bg)
        badge.pack(side='left')
        # 記住徽章不要被 hover 改色
        card = parent.master.master  # content -> card
        if hasattr(card, '_skip_bg'):
            card._skip_bg.add(id(badge))

    def _create_avatar(self, parent, name, size=24):
        """建立圓形頭像 Canvas（首字母）"""
        color = _get_avatar_color(name)
        c = tk.Canvas(parent, width=size, height=size,
                      highlightthickness=0, bg=parent.cget('bg'))
        c.create_oval(1, 1, size - 1, size - 1, fill=color, outline='')
        initial = name[0].upper() if name else '?'
        c.create_text(size // 2, size // 2, text=initial,
                      font=(FONT_FAMILY, int(size * 0.4), 'bold'),
                      fill='white')
        return c

    # ─── 懸停效果 ─────────────────────────────────────────

    def _bind_hover(self, widget, task):
        if not hasattr(widget, '_normal_bg'):
            return

        def _enter(e):
            self._set_bg_recursive(widget, widget._hover_bg,
                                   widget._skip_bg)
            widget.configure(highlightbackground='#B0C4DE')

        def _leave(e):
            self._set_bg_recursive(widget, widget._normal_bg,
                                   widget._skip_bg)
            widget.configure(highlightbackground='#E0E0E0')

        widget.bind('<Enter>', _enter)
        widget.bind('<Leave>', _leave)

    def _set_bg_recursive(self, widget, bg, skip_ids=None):
        skip = skip_ids or set()
        if id(widget) in skip:
            return
        try:
            if isinstance(widget, tk.Canvas) and widget.winfo_width() <= 14:
                return
            widget.configure(bg=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_bg_recursive(child, bg, skip)

    # ─── 右鍵選單 ────────────────────────────────────────

    def _bind_right_click(self, widget, task):
        widget.bind('<Button-3>', lambda e: self._show_context_menu(e, task))
        for child in widget.winfo_children():
            self._bind_right_click(child, task)

    def _show_context_menu(self, event, task):
        menu = tk.Menu(self, tearoff=0)
        status_menu = tk.Menu(menu, tearoff=0)
        for status in STATUSES:
            if status != task.status:
                status_menu.add_command(
                    label=status,
                    command=lambda s=status: self.on_status_change(task.id, s)
                )
        menu.add_cascade(label="變更狀態", menu=status_menu)
        menu.add_separator()
        menu.add_command(label="編輯",
                         command=lambda: self.on_task_click(task.id))
        menu.add_command(label="刪除",
                         command=lambda: self.on_task_delete(task.id))
        menu.tk_popup(event.x_root, event.y_root)


class ScrollableColumn(ttk.Frame):
    def __init__(self, parent, status_name, accent_color):
        super().__init__(parent)
        self.status_name = status_name
        self.accent_color = accent_color

        # 標題列
        header_frame = tk.Frame(self, bg='#FAFAFA')
        header_frame.pack(fill='x')

        # 色條（頂部）
        accent = tk.Frame(header_frame, bg=accent_color, height=3)
        accent.pack(fill='x')

        # 狀態名稱 + 數量氣泡
        title_row = tk.Frame(header_frame, bg='#FAFAFA')
        title_row.pack(fill='x', padx=8, pady=(6, 6))

        self.header_label = tk.Label(
            title_row, text=status_name,
            font=(FONT_FAMILY, 11, 'bold'),
            bg='#FAFAFA', fg='#333333'
        )
        self.header_label.pack(side='left')

        self.count_label = tk.Label(
            title_row, text='0',
            font=(FONT_FAMILY, 9, 'bold'),
            bg=accent_color, fg='white',
            padx=6, pady=1
        )
        self.count_label.pack(side='left', padx=(6, 0))

        # 分隔線
        tk.Frame(self, bg='#E0E0E0', height=1).pack(fill='x')

        # 捲動區域
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(container, bg='#F5F5F5', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient='vertical',
                                        command=self.canvas.yview)
        self.inner_frame = ttk.Frame(self.canvas)

        self.inner_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor='nw'
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def set_count(self, count):
        self.count_label.configure(text=str(count))

    def clear(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

    def update_scroll_region(self):
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
