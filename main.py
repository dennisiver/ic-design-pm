"""IC設計專案管理工具 - 程式進入點"""

import sys
import os
import tkinter as tk

# DPI 支援
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def get_resource_path(relative_path):
    """取得資源檔案路徑，相容 PyInstaller 打包環境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def main():
    # 確保工作目錄正確（PyInstaller 打包後可能改變）
    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)

    # 加入模組搜尋路徑
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from database import DatabaseManager
    from ui.app_window import AppWindow
    from constants import APP_NAME

    # 初始化資料庫
    db = DatabaseManager()
    db.initialize()

    # 建立主視窗
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1280x800")
    root.minsize(960, 600)

    # 嘗試設定圖示
    try:
        icon_path = get_resource_path('assets/icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except tk.TclError:
        pass

    app = AppWindow(root, db)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
