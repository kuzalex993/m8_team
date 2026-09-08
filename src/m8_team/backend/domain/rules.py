"""Pure business predicates. No I/O. Extracted from the inline checks that were tangled
into ``userPage.close_user_challenge`` and ``employees_tab.update_user_bonus``.
"""

from __future__ import annotations

from datetime import date


def completed_on_time(planned_finish: date, actual_finish: date) -> bool:
    """A challenge earns its reward only if finished on or before the planned date."""
    return actual_finish <= planned_finish


def can_afford(free_bonuses: int, price: int) -> bool:
    return free_bonuses >= price


def write_off_allowed(current_balance: int, amount: int) -> bool:
    """``amount`` is a positive magnitude to subtract."""
    return current_balance >= amount
