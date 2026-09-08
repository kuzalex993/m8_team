"""ECharts option builders for the user pages. Presentation only - stays in the UI layer."""

from __future__ import annotations

from typing import Any


def draw_bonus_chart(free_bonus: int, reserved_bonus: int) -> dict[str, Any]:
    return {
        "tooltip": {"trigger": "item"},
        "series": [
            {
                "name": "Мои бонусы",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "labelLine": {"show": False},
                "data": [
                    {"value": free_bonus, "name": "Доступно"},
                    {"value": reserved_bonus, "name": "Резерв"},
                ],
            }
        ],
    }
