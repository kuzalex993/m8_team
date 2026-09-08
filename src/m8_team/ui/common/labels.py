"""Russian UI labels <-> backend enums. The UI speaks Russian; the backend speaks enums."""

from __future__ import annotations

from m8_team.backend.domain.enums import TransactionType

# Radio labels in the admin bonus-management sub-tab.
OPERATION_LABELS: dict[str, TransactionType] = {
    "Добавить": TransactionType.CHARGE,
    "Вычесть": TransactionType.WRITE_OFF,
}
