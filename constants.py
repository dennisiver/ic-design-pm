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

# 類別徽章顏色 (fg, bg) — OpenProject 風格
CATEGORY_BADGE_COLORS = {
    'RTL設計':               ('#1A67A3', '#DBEAFE'),
    '驗證(Verification)':    ('#6B21A8', '#EDE9FE'),
    '合成(Synthesis)':       ('#0E7490', '#CFFAFE'),
    '佈局繞線(Place&Route)': ('#92400E', '#FEF3C7'),
    'DFT':                   ('#065F46', '#D1FAE5'),
    '時序分析(STA)':         ('#9A3412', '#FFEDD5'),
    '實體驗證(Physical Verification)': ('#5B21B6', '#EDE9FE'),
    'FPGA驗證':              ('#0369A1', '#E0F2FE'),
    '其他':                  ('#555555', '#F0F0F0'),
}

# 頭像圓圈背景色（依序循環使用）
AVATAR_COLORS = [
    '#4E79A7', '#E15759', '#59A14F', '#F28E2B',
    '#B07AA1', '#76B7B2', '#EDC948', '#FF9DA7',
]

# 預設類別建議（可手動輸入任何值）
DEFAULT_CATEGORIES = [
    'RTL設計',
    '驗證(Verification)',
    '合成(Synthesis)',
    '佈局繞線(Place&Route)',
    'DFT',
    '時序分析(STA)',
    '實體驗證(Physical Verification)',
    'FPGA驗證',
    '其他',
]

# 圖表配色
CHART_COLORS = [
    '#4E79A7', '#F28E2B', '#E15759', '#76B7B2',
    '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7',
    '#9C755F', '#BAB0AC',
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
APP_VERSION = '2.3.0'
DB_FOLDER_NAME = 'ICDesignPM'
DB_FILE_NAME = 'projects.db'
