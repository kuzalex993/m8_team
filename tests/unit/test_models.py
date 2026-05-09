from m8_team.components.models import (
    Challenge,
    Reward,
    User,
    UserBonus,
    UserChallenge,
    UserReward,
)

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

USER_DICT = {
    "user_email": "alice@example.com",
    "user_name": "Alice",
    "user_position": "developer",
    "user_role": "user",
    "user_free_bonuses": 100,
    "user_reserved_bonuses": 20,
    "chat_id": "123456",
    "id": "doc-user-1",
}


def test_user_to_dict_excludes_id() -> None:
    user = User.from_dict(USER_DICT)
    assert "id" not in user.to_dict()


def test_user_to_dict_contains_expected_fields() -> None:
    user = User.from_dict(USER_DICT)
    d = user.to_dict()
    assert d["user_email"] == "alice@example.com"
    assert d["user_name"] == "Alice"
    assert d["user_position"] == "developer"
    assert d["user_role"] == "user"
    assert d["user_free_bonuses"] == 100
    assert d["user_reserved_bonuses"] == 20
    assert d["chat_id"] == "123456"


def test_user_from_dict_constructs_correctly() -> None:
    user = User.from_dict(USER_DICT)
    assert user.user_email == "alice@example.com"
    assert user.user_name == "Alice"
    assert user.id == "doc-user-1"


def test_user_from_dict_doc_id_overrides_dict_id() -> None:
    user = User.from_dict(USER_DICT, doc_id="override-id")
    assert user.id == "override-id"


def test_user_from_dict_defaults_bonuses_to_zero() -> None:
    minimal = {
        "user_email": "bob@example.com",
        "user_name": "Bob",
        "user_position": "designer",
        "user_role": "user",
    }
    user = User.from_dict(minimal)
    assert user.user_free_bonuses == 0
    assert user.user_reserved_bonuses == 0


def test_user_from_dict_defaults_chat_id_to_none() -> None:
    minimal = {
        "user_email": "bob@example.com",
        "user_name": "Bob",
        "user_position": "designer",
        "user_role": "user",
    }
    user = User.from_dict(minimal)
    assert user.chat_id is None


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

REWARD_DICT = {
    "reward_description": "Coffee",
    "reward_price": 50,
    "reward_last_update": "2024-01-01T10:00:00.000000Z",
    "id": "doc-reward-1",
}


def test_reward_to_dict_excludes_id() -> None:
    reward = Reward.from_dict(REWARD_DICT)
    assert "id" not in reward.to_dict()


def test_reward_to_dict_contains_expected_fields() -> None:
    reward = Reward.from_dict(REWARD_DICT)
    d = reward.to_dict()
    assert d["reward_description"] == "Coffee"
    assert d["reward_price"] == 50
    assert d["reward_last_update"] == "2024-01-01T10:00:00.000000Z"


def test_reward_from_dict_constructs_correctly() -> None:
    reward = Reward.from_dict(REWARD_DICT)
    assert reward.reward_description == "Coffee"
    assert reward.reward_price == 50
    assert reward.id == "doc-reward-1"


def test_reward_from_dict_doc_id_overrides_dict_id() -> None:
    reward = Reward.from_dict(REWARD_DICT, doc_id="override-id")
    assert reward.id == "override-id"


def test_reward_from_dict_no_id_when_absent() -> None:
    d = {k: v for k, v in REWARD_DICT.items() if k != "id"}
    reward = Reward.from_dict(d)
    assert reward.id is None


# ---------------------------------------------------------------------------
# Challenge
# ---------------------------------------------------------------------------

CHALLENGE_DICT = {
    "challenge_description": "Run 5km",
    "challenge_reward": 200,
    "challenge_planned_time_completion": 30,
    "challenge_active": True,
    "challenge_date_update": "2024-03-15T08:00:00.000000Z",
    "id": "doc-challenge-1",
}


def test_challenge_to_dict_excludes_id() -> None:
    challenge = Challenge.from_dict(CHALLENGE_DICT)
    assert "id" not in challenge.to_dict()


def test_challenge_to_dict_contains_expected_fields() -> None:
    challenge = Challenge.from_dict(CHALLENGE_DICT)
    d = challenge.to_dict()
    assert d["challenge_description"] == "Run 5km"
    assert d["challenge_reward"] == 200
    assert d["challenge_planned_time_completion"] == 30
    assert d["challenge_active"] is True
    assert d["challenge_date_update"] == "2024-03-15T08:00:00.000000Z"


def test_challenge_from_dict_constructs_correctly() -> None:
    challenge = Challenge.from_dict(CHALLENGE_DICT)
    assert challenge.challenge_description == "Run 5km"
    assert challenge.id == "doc-challenge-1"


def test_challenge_from_dict_doc_id_overrides_dict_id() -> None:
    challenge = Challenge.from_dict(CHALLENGE_DICT, doc_id="override-id")
    assert challenge.id == "override-id"


def test_challenge_from_dict_coerces_date_update_to_str() -> None:
    d = {**CHALLENGE_DICT, "challenge_date_update": 20240315}
    challenge = Challenge.from_dict(d)
    assert isinstance(challenge.challenge_date_update, str)
    assert challenge.challenge_date_update == "20240315"


# ---------------------------------------------------------------------------
# UserChallenge
# ---------------------------------------------------------------------------

USER_CHALLENGE_DICT = {
    "user_id": "user123",
    "user_name": "Alice",
    "challenge_id": 7,
    "challenge_descripion": "Run 5km",
    "start_date": "2024-04-01",
    "planned_finish_date": "2024-05-01",
    "challenge_status": "new",
    "challenge_success": "unknown",
    "challenge_creation_date": "2024-03-30T12:00:00.000000Z",
    "fact_finish_date": None,
    "id": "doc-uc-1",
}


def test_user_challenge_to_dict_excludes_id() -> None:
    uc = UserChallenge.from_dict(USER_CHALLENGE_DICT)
    assert "id" not in uc.to_dict()


def test_user_challenge_to_dict_contains_expected_fields() -> None:
    uc = UserChallenge.from_dict(USER_CHALLENGE_DICT)
    d = uc.to_dict()
    assert d["user_id"] == "user123"
    assert d["challenge_id"] == 7
    assert d["challenge_descripion"] == "Run 5km"
    assert d["start_date"] == "2024-04-01"
    assert d["fact_finish_date"] is None


def test_user_challenge_from_dict_constructs_correctly() -> None:
    uc = UserChallenge.from_dict(USER_CHALLENGE_DICT)
    assert uc.user_name == "Alice"
    assert uc.challenge_status == "new"
    assert uc.id == "doc-uc-1"


def test_user_challenge_from_dict_doc_id_overrides_dict_id() -> None:
    uc = UserChallenge.from_dict(USER_CHALLENGE_DICT, doc_id="override-id")
    assert uc.id == "override-id"


def test_user_challenge_from_dict_defaults_fact_finish_date_to_none() -> None:
    d = {k: v for k, v in USER_CHALLENGE_DICT.items() if k != "fact_finish_date"}
    uc = UserChallenge.from_dict(d)
    assert uc.fact_finish_date is None


# ---------------------------------------------------------------------------
# UserBonus
# ---------------------------------------------------------------------------

USER_BONUS_DICT = {
    "user_id": "user123",
    "transaction_type": "charge bonus",
    "bonus_value": 500,
    "event_type": "admin",
    "date": "2024-05-01T09:00:00.000000Z",
    "event_id": "evt-abc",
    "id": "doc-ub-1",
}


def test_user_bonus_to_dict_excludes_id() -> None:
    ub = UserBonus.from_dict(USER_BONUS_DICT)
    assert "id" not in ub.to_dict()


def test_user_bonus_to_dict_contains_expected_fields() -> None:
    ub = UserBonus.from_dict(USER_BONUS_DICT)
    d = ub.to_dict()
    assert d["user_id"] == "user123"
    assert d["transaction_type"] == "charge bonus"
    assert d["bonus_value"] == 500
    assert d["event_type"] == "admin"
    assert d["event_id"] == "evt-abc"
    assert "date" in d


def test_user_bonus_from_dict_constructs_correctly() -> None:
    ub = UserBonus.from_dict(USER_BONUS_DICT)
    assert ub.bonus_value == 500
    assert ub.id == "doc-ub-1"


def test_user_bonus_from_dict_doc_id_overrides_dict_id() -> None:
    ub = UserBonus.from_dict(USER_BONUS_DICT, doc_id="override-id")
    assert ub.id == "override-id"


def test_user_bonus_from_dict_defaults_event_id_to_none() -> None:
    d = {k: v for k, v in USER_BONUS_DICT.items() if k != "event_id"}
    ub = UserBonus.from_dict(d)
    assert ub.event_id is None


# ---------------------------------------------------------------------------
# UserReward
# ---------------------------------------------------------------------------

USER_REWARD_DICT = {
    "reward_description": "Coffee",
    "reward_id": "doc-reward-1",
    "user_id": "user123",
    "user_name": "Alice",
    "user_reward_request_date": "2024-06-01T10:00:00.000000Z",
    "user_reward_status": "new",
    "user_reward_decision_date": None,
    "id": "doc-ur-1",
}


def test_user_reward_to_dict_excludes_id() -> None:
    ur = UserReward.from_dict(USER_REWARD_DICT)
    assert "id" not in ur.to_dict()


def test_user_reward_to_dict_contains_expected_fields() -> None:
    ur = UserReward.from_dict(USER_REWARD_DICT)
    d = ur.to_dict()
    assert d["reward_description"] == "Coffee"
    assert d["reward_id"] == "doc-reward-1"
    assert d["user_id"] == "user123"
    assert d["user_name"] == "Alice"
    assert d["user_reward_status"] == "new"
    assert d["user_reward_decision_date"] is None


def test_user_reward_from_dict_constructs_correctly() -> None:
    ur = UserReward.from_dict(USER_REWARD_DICT)
    assert ur.user_reward_status == "new"
    assert ur.id == "doc-ur-1"


def test_user_reward_from_dict_doc_id_overrides_dict_id() -> None:
    ur = UserReward.from_dict(USER_REWARD_DICT, doc_id="override-id")
    assert ur.id == "override-id"


def test_user_reward_from_dict_defaults_decision_date_to_none() -> None:
    d = {k: v for k, v in USER_REWARD_DICT.items() if k != "user_reward_decision_date"}
    ur = UserReward.from_dict(d)
    assert ur.user_reward_decision_date is None
