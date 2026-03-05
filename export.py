"""Excel 匯出功能"""

from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

EXPORT_COLUMNS = [
    ('編號',       'id',              8),
    ('專案',       'project_name',   20),
    ('標題',       'title',          35),
    ('狀態',       'status',         12),
    ('優先級',     'priority',       10),
    ('類別',       'category',       25),
    ('負責人',     'assignee',       15),
    ('到期日',     'due_date',       14),
    ('開始日期',   'start_date',     14),
    ('預估週數',   'estimated_weeks', 10),
    ('標籤',       'tags',           20),
    ('描述',       'description',    50),
    ('建立時間',   'created_at',     20),
    ('更新時間',   'updated_at',     20),
]

FONT_NAME = 'Microsoft JhengHei UI'


def export_tasks_to_excel(filepath, tasks, project_name="全部專案",
                          project_lookup=None, task_tags_lookup=None):
    """匯出任務至 Excel。

    Args:
        filepath: 匯出檔案路徑
        tasks: Task 物件清單
        project_name: 當前專案名稱（顯示於標題列）
        project_lookup: {project_id: project_name} 對照表
        task_tags_lookup: {task_id: [tag_name, ...]} 對照表
    """
    if project_lookup is None:
        project_lookup = {}
    if task_tags_lookup is None:
        task_tags_lookup = {}

    wb = Workbook()
    ws = wb.active
    ws.title = "任務清單"

    num_cols = len(EXPORT_COLUMNS)

    # 標題列
    ws.merge_cells(start_row=1, start_column=1,
                   end_row=1, end_column=num_cols)
    title_cell = ws.cell(row=1, column=1)
    title_cell.value = (f"專案: {project_name}  —  "
                        f"匯出時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    title_cell.font = Font(name=FONT_NAME, size=14, bold=True)
    title_cell.alignment = Alignment(horizontal='left')

    # 表頭 (第3列)
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4',
                              fill_type='solid')
    header_font = Font(name=FONT_NAME, size=10, bold=True, color='FFFFFF')
    thin_border = Border(
        bottom=Side(style='thin', color='999999')
    )

    for col_idx, (header, _, width) in enumerate(EXPORT_COLUMNS, 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # 優先級標色
    priority_fills = {
        '緊急': PatternFill(start_color='FFC7CE', end_color='FFC7CE',
                          fill_type='solid'),
        '高':   PatternFill(start_color='FFE699', end_color='FFE699',
                          fill_type='solid'),
    }

    # 狀態標色
    status_fills = {
        '已完成': PatternFill(start_color='C6EFCE', end_color='C6EFCE',
                            fill_type='solid'),
        '進行中': PatternFill(start_color='BDD7EE', end_color='BDD7EE',
                            fill_type='solid'),
    }

    body_font = Font(name=FONT_NAME, size=10)

    # 資料列 (第4列開始)
    for row_idx, task in enumerate(tasks, 4):
        for col_idx, (_, field, _) in enumerate(EXPORT_COLUMNS, 1):
            if field == 'project_name':
                value = project_lookup.get(task.project_id, '')
            elif field == 'tags':
                value = ', '.join(task_tags_lookup.get(task.id, []))
            elif field == 'estimated_weeks':
                value = task.estimated_weeks if task.estimated_weeks else ''
            else:
                value = getattr(task, field, '')

            cell = ws.cell(row=row_idx, column=col_idx, value=value or '')
            cell.font = body_font
            cell.alignment = Alignment(
                vertical='center',
                wrap_text=(field == 'description')
            )
            cell.border = thin_border

            # 條件格式
            if field == 'priority' and task.priority in priority_fills:
                cell.fill = priority_fills[task.priority]
            if field == 'status' and task.status in status_fills:
                cell.fill = status_fills[task.status]

    # 自動篩選
    if tasks:
        last_row = 3 + len(tasks)
        ws.auto_filter.ref = f"A3:{get_column_letter(num_cols)}{last_row}"

    # 凍結窗格
    ws.freeze_panes = 'A4'

    wb.save(filepath)
