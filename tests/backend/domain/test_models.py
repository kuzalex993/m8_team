from m8_team.backend.domain.models import (
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
    assert "id" not in User.from_dict(USER_DICT).to_dict()


def test_user_to_dict_contains_expected_fields() -> None:
    d = User.from_dict(USER_DICT).to_dict()
    assert d["user_email"] == "alice@example.com"
    assert d["user_free_bonuses"] == 100
    assert d["chat_id"] == "123456"


def test_user_from_dict_doc_id_overrides_dict_id() -> None:
    assert User.from_dict(USER_DICT, doc_id="override-id").id == "override-id"


def test_user_from_dict_defaults() -> None:
    minimal = {
        "user_email": "bob@example.com",
        "user_name": "Bob",
        "user_position": "designer",
        "user_role": "user",
    }
    user = User.from_dict(minimal)
    assert user.user_free_bonuses == 0
    assert user.user_reserved_bonuses == 0
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


def test_reward_roundtrip() -> None:
    reward = Reward.from_dict(REWARD_DICT)
    assert reward.reward_price == 50
    assert reward.id == "doc-reward-1"
    assert "id" not in reward.to_dict()


def test_reward_from_dict_no_id_when_absent() -> None:
    d = {k: v for k, v in REWARD_DICT.items() if k != "id"}
    assert Reward.from_dict(d).id is None


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


def test_challenge_roundtrip() -> None:
    challenge = Challenge.from_dict(CHALLENGE_DICT)
    assert challenge.challenge_reward == 200
    assert "id" not in challenge.to_dict()


def test_challenge_from_dict_coerces_date_update_to_str() -> None:
    challenge = Challenge.from_dict({**CHALLENGE_DICT, "challenge_date_update": 20240315})
    assert challenge.challenge_date_update == "20240315"


# ---------------------------------------------------------------------------
# UserChallenge - the Firestore misspelling is mapped at the boundary
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


def test_user_challenge_from_dict_maps_misspelled_field_to_description() -> None:
    uc = UserChallenge.from_dict(USER_CHALLENGE_DICT)
    assert uc.description == "Run 5km"
    assert uc.id == "doc-uc-1"


def test_user_challenge_from_dict_accepts_already_renamed_field() -> None:
    d = {k: v for k, v in USER_CHALLENGE_DICT.items() if k != "challenge_descripion"}
    d["description"] = "Renamed"
    assert UserChallenge.from_dict(d).description == "Renamed"


def test_user_challenge_to_dict_writes_misspelled_field_back() -> None:
    d = UserChallenge.from_dict(USER_CHALLENGE_DICT).to_dict()
    assert d["challenge_descripion"] == "Run 5km"
    assert "description" not in d
    assert "id" not in d


def test_user_challenge_defaults_fact_finish_date_to_none() -> None:
    d = {k: v for k, v in USER_CHALLENGE_DICT.items() if k != "fact_finish_date"}
    assert UserChallenge.from_dict(d).fact_finish_date is None


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


def test_user_bonus_roundtrip() -> None:
    ub = UserBonus.from_dict(USER_BONUS_DICT)
    assert ub.bonus_value == 500
    assert "id" not in ub.to_dict()


def test_user_bonus_defaults_event_id_to_none() -> None:
    d = {k: v for k, v in USER_BONUS_DICT.items() if k != "event_id"}
    assert UserBonus.from_dict(d).event_id is None


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


def test_user_reward_roundtrip() -> None:
    ur = UserReward.from_dict(USER_REWARD_DICT)
    assert ur.user_reward_status == "new"
    assert ur.id == "doc-ur-1"
    assert "id" not in ur.to_dict()


def test_user_reward_doc_id_overrides_dict_id() -> None:
    assert UserReward.from_dict(USER_REWARD_DICT, doc_id="x").id == "x"


def test_user_reward_defaults_decision_date_to_none() -> None:
    d = {k: v for k, v in USER_REWARD_DICT.items() if k != "user_reward_decision_date"}
    assert UserReward.from_dict(d).user_reward_decision_date is None
