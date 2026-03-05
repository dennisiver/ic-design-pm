"""Canvas 圖表繪製工具函式"""

import math
from constants import CHART_COLORS, FONT_FAMILY


def draw_donut_chart(canvas, data, cx, cy, radius, title=''):
    """繪製甜甜圈圖。data: [(label, value), ...]"""
    canvas.delete('all')
    if not data or all(v == 0 for _, v in data):
        canvas.create_text(cx, cy, text="無資料", font=(FONT_FAMILY, 10),
                           fill='#999999')
        return

    total = sum(v for _, v in data)
    inner_r = radius * 0.55
    start = 90  # 從 12 點鐘方向開始

    for i, (label, value) in enumerate(data):
        if value == 0:
            continue
        extent = -(value / total) * 360
        color = CHART_COLORS[i % len(CHART_COLORS)]
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                          start=start, extent=extent, fill=color,
                          outline='white', width=2,
                          tags=('slice', f'item_{i}'))
        start += extent

    # 中心白圓
    canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                       fill='white', outline='white')
    canvas.create_text(cx, cy - 8, text=str(total),
                       font=(FONT_FAMILY, 16, 'bold'), fill='#333333')
    canvas.create_text(cx, cy + 12, text="項任務",
                       font=(FONT_FAMILY, 9), fill='#888888')

    # 標題
    if title:
        canvas.create_text(cx, 16, text=title,
                           font=(FONT_FAMILY, 10, 'bold'), fill='#333333')

    # 圖例
    legend_y = cy + radius + 16
    legend_x = cx - radius + 10
    for i, (label, value) in enumerate(data):
        if value == 0:
            continue
        color = CHART_COLORS[i % len(CHART_COLORS)]
        canvas.create_rectangle(legend_x, legend_y, legend_x + 10, legend_y + 10,
                                fill=color, outline='')
        canvas.create_text(legend_x + 14, legend_y + 5, anchor='w',
                           text=f"{label} ({value})",
                           font=(FONT_FAMILY, 8), fill='#555555')
        legend_y += 14


def draw_bar_chart(canvas, data, x, y, width, height, title='', horizontal=False):
    """繪製長條圖。data: [(label, value), ...]"""
    canvas.delete('all')
    if not data or all(v == 0 for _, v in data):
        canvas.create_text(x + width // 2, y + height // 2, text="無資料",
                           font=(FONT_FAMILY, 10), fill='#999999')
        return

    max_val = max(v for _, v in data)
    if max_val == 0:
        max_val = 1

    if title:
        canvas.create_text(x + width // 2, y + 4, text=title, anchor='n',
                           font=(FONT_FAMILY, 10, 'bold'), fill='#333333')

    if horizontal:
        # 水平長條圖
        bar_area_y = y + 24
        bar_area_h = height - 30
        bar_h = min(22, bar_area_h // max(len(data), 1) - 4)
        label_w = 70

        for i, (label, value) in enumerate(data):
            by = bar_area_y + i * (bar_h + 4)
            bw = (value / max_val) * (width - label_w - 40)
            color = CHART_COLORS[i % len(CHART_COLORS)]

            # 標籤
            canvas.create_text(x + label_w - 4, by + bar_h // 2, anchor='e',
                               text=label[:6], font=(FONT_FAMILY, 8), fill='#555555')
            # 長條
            if bw > 0:
                canvas.create_rectangle(x + label_w, by, x + label_w + bw,
                                        by + bar_h, fill=color, outline='')
            # 數值
            canvas.create_text(x + label_w + bw + 4, by + bar_h // 2, anchor='w',
                               text=str(value), font=(FONT_FAMILY, 8, 'bold'),
                               fill='#333333')
    else:
        # 垂直長條圖
        bar_area_x = x + 10
        bar_area_w = width - 20
        bar_area_y = y + 24
        bar_area_h = height - 50
        bar_w = min(36, bar_area_w // max(len(data), 1) - 6)
        total_w = len(data) * (bar_w + 6)
        start_x = bar_area_x + (bar_area_w - total_w) // 2

        for i, (label, value) in enumerate(data):
            bx = start_x + i * (bar_w + 6)
            bh = (value / max_val) * bar_area_h if max_val else 0
            by = bar_area_y + bar_area_h - bh
            color = CHART_COLORS[i % len(CHART_COLORS)]

            if bh > 0:
                canvas.create_rectangle(bx, by, bx + bar_w,
                                        bar_area_y + bar_area_h,
                                        fill=color, outline='')
            # 數值
            canvas.create_text(bx + bar_w // 2, by - 4, text=str(value),
                               font=(FONT_FAMILY, 8, 'bold'),
                               fill='#333333', anchor='s')
            # 標籤
            canvas.create_text(bx + bar_w // 2, bar_area_y + bar_area_h + 6,
                               text=label[:4], font=(FONT_FAMILY, 8),
                               fill='#555555', anchor='n')
