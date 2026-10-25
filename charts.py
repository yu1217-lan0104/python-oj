"""服务端生成 SVG 图表（零 JS 依赖，离线可用，也能直接嵌进导出的报告）。"""

import math
from html import escape

from markupsafe import Markup

PALETTE = ["#2f6bff", "#10b7a3", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9", "#64748b"]
FONT = "Microsoft YaHei, PingFang SC, system-ui, sans-serif"


def _svg(width: int, height: int, body: list) -> Markup:
    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" height="auto" role="img" style="font-family:{FONT};">'
    )
    return Markup(head + "".join(body) + "</svg>")


def donut_chart(slices, size: int = 220, thickness: int = 26, center_label: str = "提交") -> Markup:
    """slices: [(label, value, color)]"""
    total = sum(int(v) for _, v, _ in slices)
    radius = (size - thickness) / 2
    cx = cy = size / 2
    circumference = 2 * math.pi * radius
    body = [
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#eef2f8" '
        f'stroke-width="{thickness}" />'
    ]

    start = 0.0
    for _label, value, color in slices:
        if value <= 0:
            continue
        length = circumference * value / total
        body.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="{thickness}" stroke-dasharray="{length:.2f} {circumference - length:.2f}" '
            f'stroke-dashoffset="{-start:.2f}" transform="rotate(-90 {cx} {cy})" />'
        )
        start += length

    body.append(
        f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="26" font-weight="800" '
        f'fill="#101828">{total}</text>'
    )
    body.append(
        f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="12" fill="#6b7a90">'
        f"{escape(center_label)}</text>"
    )
    return _svg(size, size, body)


def line_chart(points, width: int = 620, height: int = 240) -> Markup:
    """points: [(label, value)]，用于最近 N 天的提交趋势。"""
    pad_l, pad_r, pad_t, pad_b = 40, 14, 18, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    values = [v for _, v in points] or [0]
    max_v = max(max(values), 1)
    step = plot_w / max(len(points) - 1, 1)

    body = []
    # 横向网格线 + 纵轴刻度
    for i in range(5):
        y = pad_t + plot_h * i / 4
        value = round(max_v * (4 - i) / 4)
        body.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
            f'stroke="#eef2f8" stroke-width="1" />'
        )
        body.append(
            f'<text x="{pad_l - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
            f'fill="#98a2b3">{value}</text>'
        )

    coords = []
    for i, (_label, value) in enumerate(points):
        x = pad_l + i * step
        y = pad_t + plot_h * (1 - value / max_v)
        coords.append((x, y))

    if coords:
        area = (
            f"M {coords[0][0]:.1f} {pad_t + plot_h:.1f} "
            + " ".join(f"L {x:.1f} {y:.1f}" for x, y in coords)
            + f" L {coords[-1][0]:.1f} {pad_t + plot_h:.1f} Z"
        )
        body.append(f'<path d="{area}" fill="#2f6bff" fill-opacity="0.10" stroke="none" />')
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        body.append(
            f'<polyline points="{poly}" fill="none" stroke="#2f6bff" stroke-width="2.5" '
            'stroke-linejoin="round" stroke-linecap="round" />'
        )
        for (x, y), (_label, value) in zip(coords, points):
            if value:
                body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#fff" stroke="#2f6bff" stroke-width="2" />')

    # 横轴标签（每 2 个显示一个，避免拥挤）
    for i, (label, _value) in enumerate(points):
        if i % 2 == 0 or i == len(points) - 1:
            x = pad_l + i * step
            body.append(
                f'<text x="{x:.1f}" y="{height - 8}" text-anchor="middle" font-size="10.5" '
                f'fill="#98a2b3">{escape(str(label))}</text>'
            )
    return _svg(width, height, body)


def bar_chart(items, width: int = 620, row_height: int = 34, label_width: int = 86) -> Markup:
    """items: [(label, solved, total)]，画成横向进度条。"""
    height = row_height * max(len(items), 1) + 8
    track_x = label_width
    track_w = width - label_width - 64
    body = []
    for i, (label, solved, total) in enumerate(items):
        y = 4 + i * row_height
        percent = (solved / total) if total else 0
        bar_w = max(track_w * percent, 0)
        color = PALETTE[i % len(PALETTE)]
        body.append(
            f'<text x="0" y="{y + 17}" font-size="12" font-weight="700" fill="#344054">'
            f"{escape(str(label))}</text>"
        )
        body.append(
            f'<rect x="{track_x}" y="{y + 8}" width="{track_w}" height="10" rx="5" fill="#eef2f8" />'
        )
        if bar_w > 0:
            body.append(
                f'<rect x="{track_x}" y="{y + 8}" width="{bar_w:.1f}" height="10" rx="5" '
                f'fill="{color}" />'
            )
        body.append(
            f'<text x="{width - 4}" y="{y + 17}" text-anchor="end" font-size="11.5" '
            f'fill="#6b7a90">{solved}/{total}</text>'
        )
    return _svg(width, height, body)
