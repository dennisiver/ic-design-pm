"""看板視圖：四欄看板（待辦/進行中/審核中/已完成）"""

import tkinter as tk
import tkinter.ttk as ttk
from constants import (STATUSES, STATUS_COLORS, PRIORITY_COLORS,
                       PRIORITY_BG, FONT_BODY_BOLD, FONT_SMALL, FONT_FAMILY)


class KanbanView(ttk.Frame):
    def __init__(self, parent, on_task_click, on_status_change, on_task_delete):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self.on_status_change = on_status_change
        self.on_task_delete = on_task_delete

        self.columns = {}
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

    def _create_card(self, parent, task):
        bg = PRIORITY_BG.get(task.priority, '#FFFFFF')

        card = tk.Frame(parent, bg=bg, relief='groove', bd=1,
                        cursor='hand2', padx=8, pady=6)

        # 優先級圓點 + 標題
        title_frame = tk.Frame(card, bg=bg)
        title_frame.pack(fill='x')

        priority_color = PRIORITY_COLORS.get(task.priority, '#6C757D')
        dot = tk.Canvas(title_frame, width=10, height=10, bg=bg,
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=priority_color, outline='')
        dot.pack(side='left', padx=(0, 4), pady=2)

        title_label = tk.Label(title_frame, text=task.title, bg=bg,
                               font=FONT_BODY_BOLD, anchor='w',
                               wraplength=180, justify='left')
        title_label.pack(side='left', fill='x', expand=True)

        # 類別
        if task.category:
            cat_label = tk.Label(card, text=task.category, bg=bg,
                                 font=FONT_SMALL, fg='#6C757D', anchor='w')
            cat_label.pack(fill='x')

        # 負責人 + 到期日
        info_parts = []
        if task.assignee:
            info_parts.append(f"\u8ca0\u8cac\u4eba: {task.assignee}")
        if task.due_date:
            info_parts.append(f"\u5230\u671f: {task.due_date}")
        if info_parts:
            info_label = tk.Label(card, text="  |  ".join(info_parts), bg=bg,
                                  font=FONT_SMALL, fg='#888888', anchor='w')
            info_label.pack(fill='x')

        # 綁定事件到卡片和所有子元件
        self._bind_card_events(card, task)
        return card

    def _bind_card_events(self, widget, task):
        widget.bind('<Button-1>', lambda e: self.on_task_click(task.id))
        widget.bind('<Button-3>', lambda e: self._show_context_menu(e, task))
        for child in widget.winfo_children():
            self._bind_card_events(child, task)

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

        # 標題
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x')

        self.header_label = ttk.Label(
            header_frame,
            text=f"{status_name} (0)",
            font=(FONT_FAMILY, 11, 'bold')
        )
        self.header_label.pack(anchor='w', padx=8, pady=(8, 2))

        # 色條
        accent = tk.Frame(self, bg=accent_color, height=3)
        accent.pack(fill='x', padx=4)

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
        self.header_label.configure(text=f"{self.status_name} ({count})")

    def clear(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

    def update_scroll_region(self):
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
