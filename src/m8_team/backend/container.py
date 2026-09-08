"""Composition root: wire :class:`Config` -> Firestore client -> repositories -> services.

The UI builds one :class:`Container` per session (see ``m8_team.ui.container``) and only ever
touches ``Container.<service>``.
"""

from __future__ import annotations

from dataclasses import dataclass

from m8_team.backend.config import Config
from m8_team.backend.notifications.telegram import TelegramClient
from m8_team.backend.repositories.bonus_ledger_repo import BonusLedgerRepo
from m8_team.backend.repositories.challenges_repo import ChallengesRepo
from m8_team.backend.repositories.credentials_repo import CredentialsRepo
from m8_team.backend.repositories.firestore import get_client
from m8_team.backend.repositories.rewards_repo import RewardsRepo
from m8_team.backend.repositories.user_challenge_repo import UserChallengeRepo
from m8_team.backend.repositories.user_reward_repo import UserRewardRepo
from m8_team.backend.repositories.users_repo import UsersRepo
from m8_team.backend.services.auth_service import AuthService
from m8_team.backend.services.bonus_service import BonusService
from m8_team.backend.services.challenge_service import ChallengeService
from m8_team.backend.services.notification_service import NotificationService
from m8_team.backend.services.reward_service import RewardService
from m8_team.backend.services.stats_service import StatsService
from m8_team.backend.services.user_service import UserService


@dataclass(frozen=True)
class Container:
    config: Config
    auth: AuthService
    user: UserService
    bonus: BonusService
    challenge: ChallengeService
    reward: RewardService
    stats: StatsService


def build_container(config: Config | None = None) -> Container:
    config = config or Config.from_env()
    client = get_client(config)

    users_repo = UsersRepo(client)
    credentials_repo = CredentialsRepo(client)
    challenges_repo = ChallengesRepo(client)
    rewards_repo = RewardsRepo(client)
    user_challenge_repo = UserChallengeRepo(client)
    user_reward_repo = UserRewardRepo(client)
    bonus_ledger_repo = BonusLedgerRepo(client)

    telegram = TelegramClient(config.bot_token)
    notifications = NotificationService(users_repo, telegram)

    user_service = UserService(users_repo)

    return Container(
        config=config,
        auth=AuthService(credentials_repo),
        user=user_service,
        bonus=BonusService(bonus_ledger_repo, user_service, notifications),
        challenge=ChallengeService(
            challenges_repo, user_challenge_repo, bonus_ledger_repo, notifications
        ),
        reward=RewardService(
            rewards_repo,
            user_reward_repo,
            user_service,
            bonus_ledger_repo,
            notifications,
        ),
        stats=StatsService(user_challenge_repo, bonus_ledger_repo, user_service),
    )
