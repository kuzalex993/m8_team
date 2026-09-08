"""The admin sidebar menu - single source of truth pairing each label with its icon."""

from __future__ import annotations

from typing import NamedTuple


class MenuItem(NamedTuple):
    label: str
    icon: str


MENU_ITEMS = [
    MenuItem("Сотрудники", "house"),
    MenuItem("Задания", "list-task"),
    MenuItem("Награды", "award"),
    MenuItem("Запросы", "inbox"),
    MenuItem("Статистика", "bar-chart"),
]
