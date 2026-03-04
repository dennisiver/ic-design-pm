"""列表視圖：Treeview 表格，可排序"""

import tkinter as tk
import tkinter.ttk as ttk
from constants import STATUSES, FONT_FAMILY


COLUMNS = [
    ('title',      '標題',   250),
    ('status',     '狀態',    80),
    ('priority',   '優先級',  70),
    ('category',   '類別',   150),
    ('assignee',   '負責人', 100),
    ('due_date',   '到期日', 100),
    ('created_at', '建立時間', 140),
]


class ListView(ttk.Frame):
    def __init__(self, parent, on_task_click, on_status_change, on_task_delete):
        super().__init__(parent)
        self.on_task_click = on_task_click
        self.on_status_change = on_status_change
        self.on_task_delete = on_task_delete
        self.tasks_map = {}  # iid -> task
        self.sort_col = 'priority'
        self.sort_reverse = False

        # Treeview
        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(self, columns=col_ids, show='headings',
                                 selectmode='browse')

        for col_id, heading, width in COLUMNS:
            self.tree.heading(col_id, text=heading,
                              command=lambda c=col_id: self._sort_by(c))
            self.tree.column(col_id, width=width, minwidth=50)

        # 捲軸
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # 事件
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

    def refresh(self, tasks):
        self.tree.delete(*self.tree.get_children())
        self.tasks_map.clear()

        for task in tasks:
            iid = str(task.id)
            values = (
                task.title,
                task.status,
                task.priority,
                task.category,
                task.assignee,
                task.due_date or '',
                task.created_at,
            )
            self.tree.insert('', 'end', iid=iid, values=values)
            self.tasks_map[iid] = task

    def _sort_by(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False

        items = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children()]
        items.sort(reverse=self.sort_reverse)
        for index, (_, iid) in enumerate(items):
            self.tree.move(iid, '', index)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and item in self.tasks_map:
            self.on_task_click(self.tasks_map[item].id)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item not in self.tasks_map:
            return
        self.tree.selection_set(item)
        task = self.tasks_map[item]

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
