"""Domain errors raised by services and mapped to UI feedback by ``m8_team.ui.common.feedback``."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all expected, user-meaningful failures in the backend."""


class InsufficientBalance(DomainError):
    """A write-off / spend would drive ``user_free_bonuses`` negative."""


class InsufficientReservedBonuses(DomainError):
    """A reward confirmation exceeds the user's ``user_reserved_bonuses``."""


class NotFound(DomainError):
    """A referenced document (user, reward, challenge, ...) does not exist."""


class PersistenceError(DomainError):
    """A Firestore write failed. Wraps the underlying SDK exception message."""
