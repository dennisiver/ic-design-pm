"""ttk 主題與樣式配置 — OpenProject 風格"""

import tkinter.ttk as ttk
from constants import FONT_FAMILY


def setup_styles(root):
    style = ttk.Style()
    available = style.theme_names()
    if 'vista' in available:
        style.theme_use('vista')
    elif 'clam' in available:
        style.theme_use('clam')

    style.configure('.', font=(FONT_FAMILY, 10))

    # Treeview — 加高列高、交替行色
    style.configure('Treeview',
                    font=(FONT_FAMILY, 10),
                    rowheight=32)
    style.configure('Treeview.Heading',
                    font=(FONT_FAMILY, 10, 'bold'),
                    padding=(4, 6))

    # Toolbar buttons
    style.configure('Toolbar.TButton',
                    font=(FONT_FAMILY, 10),
                    padding=(10, 4))

    # Accent button（主要操作按鈕）
    style.configure('Accent.TButton',
                    font=(FONT_FAMILY, 10, 'bold'),
                    padding=(12, 5))

    # Tab buttons (分頁) — OpenProject 扁平分頁風格
    style.configure('Tab.TButton',
                    font=(FONT_FAMILY, 10),
                    padding=(16, 6),
                    relief='flat')

    style.configure('ActiveTab.TButton',
                    font=(FONT_FAMILY, 10, 'bold'),
                    padding=(16, 6),
                    relief='flat')

    # Label styles
    style.configure('Header.TLabel',
                    font=(FONT_FAMILY, 12, 'bold'))
    style.configure('Title.TLabel',
                    font=(FONT_FAMILY, 14, 'bold'))
    style.configure('Small.TLabel',
                    font=(FONT_FAMILY, 9))
    style.configure('Status.TLabel',
                    font=(FONT_FAMILY, 9),
                    foreground='#555555')

    # Dashboard styles
    style.configure('DashCard.TFrame',
                    relief='groove',
                    borderwidth=1)
    style.configure('BigNumber.TLabel',
                    font=(FONT_FAMILY, 22, 'bold'))

    # 看板欄標題
    style.configure('ColumnHeader.TLabel',
                    font=(FONT_FAMILY, 11, 'bold'))

    root.configure(bg='#F0F0F0')
