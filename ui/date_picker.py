"""日曆日期選擇器：純 tkinter Canvas 實作"""

import tkinter as tk
import tkinter.ttk as ttk
import calendar
from datetime import date, datetime
from constants import FONT_FAMILY, FONT_BODY, FONT_BODY_BOLD


class CalendarPopup(tk.Toplevel):
    """點擊後彈出的月曆視窗"""

    def __init__(self, parent, selected_date=None, on_select=None):
        super().__init__(parent)
        self.overrideredirect(True)  # 無邊框
        self.on_select = on_select
        self.result = None

        if selected_date:
            try:
                d = datetime.strptime(selected_date, '%Y-%m-%d').date()
                self.year = d.year
                self.month = d.month
                self.selected = d
            except ValueError:
                today = date.today()
                self.year = today.year
                self.month = today.month
                self.selected = None
        else:
            today = date.today()
            self.year = today.year
            self.month = today.month
            self.selected = None

        self._build()
        self._draw()

        # 點選外部關閉
        self.bind('<FocusOut>', lambda e: self._close())
        self.focus_set()
        self.grab_set()

    def _build(self):
        self.configure(bg='white', relief='solid', bd=1)

        # 導覽列
        nav = tk.Frame(self, bg='white')
        nav.pack(fill='x', padx=4, pady=(4, 0))

        tk.Button(nav, text='<<', font=(FONT_FAMILY, 8), width=3, bd=0,
                  bg='white', command=self._prev_year).pack(side='left')
        tk.Button(nav, text='<', font=(FONT_FAMILY, 8), width=3, bd=0,
                  bg='white', command=self._prev_month).pack(side='left')

        self.title_label = tk.Label(nav, text='', font=(FONT_FAMILY, 10, 'bold'),
                                     bg='white')
        self.title_label.pack(side='left', expand=True)

        tk.Button(nav, text='>', font=(FONT_FAMILY, 8), width=3, bd=0,
                  bg='white', command=self._next_month).pack(side='right')
        tk.Button(nav, text='>>', font=(FONT_FAMILY, 8), width=3, bd=0,
                  bg='white', command=self._next_year).pack(side='right')

        # 星期標頭
        days_frame = tk.Frame(self, bg='white')
        days_frame.pack(fill='x', padx=4)
        day_names = ['一', '二', '三', '四', '五', '六', '日']
        for i, name in enumerate(day_names):
            fg = '#DC3545' if i >= 5 else '#333333'
            tk.Label(days_frame, text=name, width=4,
                     font=(FONT_FAMILY, 9, 'bold'), bg='white', fg=fg).grid(
                row=0, column=i)

        # 日期格
        self.day_frame = tk.Frame(self, bg='white')
        self.day_frame.pack(fill='both', padx=4, pady=(0, 4))

        # 今天按鈕 + 清除
        bottom = tk.Frame(self, bg='white')
        bottom.pack(fill='x', padx=4, pady=(0, 4))
        tk.Button(bottom, text='今天', font=(FONT_FAMILY, 8), bd=0,
                  bg='#E8F0FE', command=self._select_today).pack(side='left', padx=2)
        tk.Button(bottom, text='清除', font=(FONT_FAMILY, 8), bd=0,
                  bg='#FFF0F0', command=self._clear).pack(side='left', padx=2)

    def _draw(self):
        self.title_label.configure(text=f'{self.year} / {self.month:02d}')

        # 清除日期格
        for w in self.day_frame.winfo_children():
            w.destroy()

        cal = calendar.monthcalendar(self.year, self.month)
        today = date.today()

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self.day_frame, text='', width=4,
                             bg='white').grid(row=r, column=c)
                    continue

                d = date(self.year, self.month, day)
                bg = 'white'
                fg = '#333333'

                if d == today:
                    bg = '#E8F0FE'
                    fg = '#0D6EFD'
                if self.selected and d == self.selected:
                    bg = '#4472C4'
                    fg = 'white'
                if c >= 5:  # 週末
                    fg = '#DC3545' if bg == 'white' else fg

                btn = tk.Label(self.day_frame, text=str(day), width=4,
                               font=(FONT_FAMILY, 9), bg=bg, fg=fg,
                               cursor='hand2', relief='flat')
                btn.grid(row=r, column=c, padx=1, pady=1)
                btn.bind('<Button-1>', lambda e, dd=d: self._on_day_click(dd))
                btn.bind('<Enter>',
                         lambda e, w=btn: w.configure(bg='#D0E0F0')
                         if w.cget('bg') != '#4472C4' else None)
                btn.bind('<Leave>',
                         lambda e, w=btn, ob=bg: w.configure(bg=ob))

    def _on_day_click(self, d):
        self.result = d.isoformat()
        if self.on_select:
            self.on_select(self.result)
        self._close()

    def _prev_month(self):
        if self.month == 1:
            self.year -= 1
            self.month = 12
        else:
            self.month -= 1
        self._draw()

    def _next_month(self):
        if self.month == 12:
            self.year += 1
            self.month = 1
        else:
            self.month += 1
        self._draw()

    def _prev_year(self):
        self.year -= 1
        self._draw()

    def _next_year(self):
        self.year += 1
        self._draw()

    def _select_today(self):
        today = date.today()
        self.result = today.isoformat()
        if self.on_select:
            self.on_select(self.result)
        self._close()

    def _clear(self):
        self.result = ''
        if self.on_select:
            self.on_select('')
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class DateEntry(ttk.Frame):
    """日期輸入元件：Entry + 日曆按鈕"""

    def __init__(self, parent, textvariable=None, **kwargs):
        super().__init__(parent)
        self.var = textvariable or tk.StringVar()

        self.entry = ttk.Entry(self, textvariable=self.var,
                                font=FONT_BODY, width=12)
        self.entry.pack(side='left', fill='x', expand=True)

        self.btn = ttk.Button(self, text='\U0001f4c5', width=3,
                               command=self._open_calendar)
        self.btn.pack(side='left', padx=(2, 0))

    def _open_calendar(self):
        # 計算彈出位置
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        popup = CalendarPopup(
            self.winfo_toplevel(),
            selected_date=self.var.get(),
            on_select=self._on_select
        )
        popup.geometry(f'+{x}+{y}')

    def _on_select(self, date_str):
        self.var.set(date_str)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)
