"""常數定義：狀態、優先級、類別、顏色、字體"""

# 任務狀態
STATUSES = ['待辦', '進行中', '審核中', '已完成']

STATUS_COLORS = {
    '待辦':   '#6C757D',
    '進行中': '#0D6EFD',
    '審核中': '#FD7E14',
    '已完成': '#198754',
}

# 優先級
PRIORITIES = ['緊急', '高', '中', '低']

PRIORITY_COLORS = {
    '緊急': '#DC3545',
    '高':   '#FD7E14',
    '中':   '#6C757D',
    '低':   '#0DCAF0',
}

PRIORITY_BG = {
    '緊急': '#FFF0F0',
    '高':   '#FFF8F0',
    '中':   '#FFFFFF',
    '低':   '#F0F8FF',
}

# IC 設計工作類別
IC_CATEGORIES = [
    'RTL設計',
    '驗證(Verification)',
    '合成(Synthesis)',
    '佈局繞線(Place&Route)',
    'DFT',
    '時序分析(STA)',
    '實體驗證(Physical Verification)',
    '其他',
]

# 字體
FONT_FAMILY = 'Microsoft JhengHei UI'
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, 'bold')
FONT_HEADER = (FONT_FAMILY, 12, 'bold')
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 14, 'bold')

# 應用程式資訊
APP_NAME = 'IC設計專案管理工具'
APP_VERSION = '1.0.0'
DB_FOLDER_NAME = 'ICDesignPM'
DB_FILE_NAME = 'projects.db'
