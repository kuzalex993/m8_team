from unittest.mock import MagicMock

from m8_team.backend.repositories.users_repo import UsersRepo


def test_create_writes_is_active_true() -> None:
    client = MagicMock()
    assert UsersRepo(client).create(email="a@b.c", username="a", name="A")
    data = client.collection.return_value.document.return_value.set.call_args.args[0]
    assert data["is_active"] is True


def test_set_active_updates_only_that_field() -> None:
    client = MagicMock()
    assert UsersRepo(client).set_active("a", False)
    client.collection.return_value.document.return_value.update.assert_called_once_with(
        {"is_active": False}
    )
