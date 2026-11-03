from m8_team.backend.domain.enums import RewardStatus, TransactionType


def test_persisted_reward_vocabulary() -> None:
    assert {status.name: status.value for status in RewardStatus} == {
        "NEW": "new",
        "COMPLETED": "completed",
        "CANCELLED": "cancelled",
    }
    assert {kind.name: kind.value for kind in TransactionType} == {
        "CHARGE": "charge bonus",
        "WRITE_OFF": "write off bonus",
        "RESERVE": "reserve bonus",
        "DEBIT": "debiting bonus",
        "REFUND": "refund bonus",
    }
