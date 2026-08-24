"""Shared constants for the admin page: Firestore collection names, the sidebar menu, and the
bonus-transaction type mapping - kept here so no tab module hardcodes its own copy."""

from typing import NamedTuple

# Firestore collection names, kept in one place instead of repeated string literals.
USERS_COLLECTION = "users"
REWARDS_COLLECTION = "rewards"
CHALLENGES_COLLECTION = "challenges"
USER_CHALLENGE_COLLECTION = "user_challenge"
USER_REWARD_COLLECTION = "user_reward"
USER_BONUS_COLLECTION = "user_bonus"

# Accounts that are not real employees and should not show up in the "Сотрудники" picker.
EXCLUDED_FROM_EMPLOYEE_LIST = {"admin", "alekseik", "alekseikuzmin", "elenabelokopytova"}

TRANSACTION_TYPE_MAP = {
    "Добавить": "charge bonus",
    "Вычесть": "write off bonus",
    "Зарезирвировать": "reserve bonus",
}


class MenuItem(NamedTuple):
    label: str
    icon: str


# Single source of truth for the sidebar menu: keeps each label paired with its icon so the
# two lists can never drift out of sync the way they previously did in show_admin_page().
MENU_ITEMS = [
    MenuItem("Сотрудники", "house"),
    MenuItem("Задания", "list-task"),
    MenuItem("Награды", "award"),
    MenuItem("Запросы", "inbox"),
    MenuItem("Статистика", "bar-chart"),
]
