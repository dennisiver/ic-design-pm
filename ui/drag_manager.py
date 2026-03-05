"""看板卡片拖放管理器"""

import tkinter as tk


class DragManager:
    THRESHOLD = 5

    def __init__(self, kanban_view):
        self.kanban = kanban_view
        self.state = 'IDLE'
        self.task = None
        self.float_win = None
        self.start_x = 0
        self.start_y = 0
        self.offset_x = 0
        self.offset_y = 0
        self._orig_col_bg = {}

    def bind_card(self, card, task):
        """綁定拖拉事件到卡片及其所有子元件"""
        def _bind(w):
            w.bind('<ButtonPress-1>', lambda e: self._on_press(e, task))
            w.bind('<B1-Motion>', self._on_motion)
            w.bind('<ButtonRelease-1>', self._on_release)
            for child in w.winfo_children():
                _bind(child)
        _bind(card)

    def _on_press(self, event, task):
        self.state = 'POTENTIAL_DRAG'
        self.task = task
        self.start_x = event.x_root
        self.start_y = event.y_root

    def _on_motion(self, event):
        if self.state == 'POTENTIAL_DRAG':
            dx = abs(event.x_root - self.start_x)
            dy = abs(event.y_root - self.start_y)
            if dx + dy > self.THRESHOLD:
                self._start_drag(event)
        elif self.state == 'DRAGGING':
            self._update_drag(event)

    def _start_drag(self, event):
        self.state = 'DRAGGING'
        # 建立浮動視窗
        self.float_win = tk.Toplevel(self.kanban)
        self.float_win.overrideredirect(True)
        try:
            self.float_win.attributes('-alpha', 0.75)
        except tk.TclError:
            pass
        # 簡化卡片外觀
        lbl = tk.Label(self.float_win, text=self.task.title,
                       bg='#E3F2FD', fg='#1565C0', padx=12, pady=8,
                       font=('Microsoft JhengHei UI', 10, 'bold'),
                       relief='raised', bd=1, wraplength=180)
        lbl.pack()
        self.float_win.update_idletasks()
        w = self.float_win.winfo_width()
        h = self.float_win.winfo_height()
        self.offset_x = w // 2
        self.offset_y = h // 2
        self.float_win.geometry(
            f'+{event.x_root - self.offset_x}+{event.y_root - self.offset_y}')

    def _update_drag(self, event):
        if self.float_win:
            self.float_win.geometry(
                f'+{event.x_root - self.offset_x}+{event.y_root - self.offset_y}')
        # 高亮目標欄位
        for status, col in self.kanban.columns.items():
            cx = col.winfo_rootx()
            cw = col.winfo_width()
            if cx <= event.x_root <= cx + cw:
                if status != self.task.status:
                    col.canvas.configure(bg='#E3F2FD')
                else:
                    col.canvas.configure(bg='#F5F5F5')
            else:
                col.canvas.configure(bg='#F5F5F5')

    def _on_release(self, event):
        if self.state == 'POTENTIAL_DRAG':
            # 視為點擊
            self.state = 'IDLE'
            if self.task:
                self.kanban.on_task_click(self.task.id)
            return

        if self.state == 'DRAGGING':
            # 清除浮動視窗
            if self.float_win:
                self.float_win.destroy()
                self.float_win = None

            # 還原所有欄位背景
            for col in self.kanban.columns.values():
                col.canvas.configure(bg='#F5F5F5')

            # 偵測目標欄位
            if self.task:
                for status, col in self.kanban.columns.items():
                    cx = col.winfo_rootx()
                    cw = col.winfo_width()
                    if cx <= event.x_root <= cx + cw:
                        if status != self.task.status:
                            self.kanban.on_status_change(self.task.id, status)
                        break

        self.state = 'IDLE'
        self.task = None
