"""Domain-level constants that are policy, not configuration."""

from __future__ import annotations

# Accounts that are not real employees: hidden from employee pickers and excluded from
# aggregate statistics. Moved from ``components/admin/constants.py``.
EXCLUDED_EMPLOYEE_IDS: frozenset[str] = frozenset(
    {"admin", "alekseik", "alekseikuzmin", "elenabelokopytova"}
)
