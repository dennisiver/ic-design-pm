"""ttk 主題與樣式配置"""

import tkinter.ttk as ttk
from constants import FONT_FAMILY


def setup_styles(root):
    style = ttk.Style()
    # Use 'clam' theme for cross-platform consistent look
    available = style.theme_names()
    if 'vista' in available:
        style.theme_use('vista')
    elif 'clam' in available:
        style.theme_use('clam')

    style.configure('.', font=(FONT_FAMILY, 10))

    # Treeview
    style.configure('Treeview',
                    font=(FONT_FAMILY, 10),
                    rowheight=28)
    style.configure('Treeview.Heading',
                    font=(FONT_FAMILY, 10, 'bold'))

    # Toolbar buttons
    style.configure('Toolbar.TButton',
                    font=(FONT_FAMILY, 10),
                    padding=(10, 4))

    # Accent button
    style.configure('Accent.TButton',
                    font=(FONT_FAMILY, 10, 'bold'),
                    padding=(12, 5))

    # Tab buttons (分頁)
    style.configure('Tab.TButton',
                    font=(FONT_FAMILY, 10),
                    padding=(14, 5),
                    relief='flat')

    style.configure('ActiveTab.TButton',
                    font=(FONT_FAMILY, 10, 'bold'),
                    padding=(14, 5),
                    relief='sunken')

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

    root.configure(bg='#F0F0F0')
