from dataclasses import dataclass
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List

from controllers.base.user import UserBase
from controllers.exceptions.user import (
    InvalidStatus, InvalidRole, CodeNotExists,
    CodeLimitReached, CodeAlreadyExists
)
from controllers.json import JsonBaseController
from databases.models import Profit, ProfitType as ProfitTypeModel
from databases.models import User
from databases.models import UserRoles as UserRole
from databases.models import UserGroup
from databases.models import UserCode
from repo.payments import Currencies
from repo.user.status import Status as UserStatus

Base = declarative_base()


class ProfitTypeId:
    FIRST_PAYMENT = 1
    MULTIPLIED_PAYMENT = 2
    REFUND = 3
    DIRECT_PAYMENT = 4
    CASH_OUT = 5


@dataclass
class UserStatistics:
    mammoth_total_ru: int = 0
    profits_sum_ru: int = 0
    mammoth_total_by: int = 0
    profits_sum_by: int = 0


@dataclass
class UserTotalStatistics(UserStatistics):
    day_earn_average_ru: int = 0
    day_earn_average_by: int = 0


@dataclass
class UserTodayStatistics(UserStatistics):
    today_earnings_ru: int = 0
    today_earnings_by: int = 0


class UserController(UserBase):
    tag_disallowed_groups = [1]  # Newbie

    def __init__(self, user_instance: User, user_service: 'UserService'):
        self._user_instance = user_instance
        self._user_service = user_service

    @property
    def id(self) -> int:
        return self._user_instance.id

    @property
    def tag(self) -> Optional[str]:
        return self._user_instance.tag

    @property
    def username(self) -> Optional[str]:
        return self._user_instance.username

    @property
    def text_id(self) -> str:
        return "#" + self.tag if self.tag else f"@{self.username}"

    async def is_banned(self, session: AsyncSession) -> bool:
        return await self.get_status(session) == UserStatus.BLOCKED

    async def is_admin(self, session: AsyncSession) -> bool:
        role = await self.get_role(session)
        return role.id in UserRole.SUPER_ROLE_ID_LIST

    async def get_stats(self, session: AsyncSession, total: bool = False) -> UserTodayStatistics | UserTotalStatistics:
        return await self._get_today_stats(session) if not total else await self._get_total_stats(session)

    async def _get_today_stats(self, session: AsyncSession) -> UserTodayStatistics:
        today = func.current_date()
        results = await session.execute(select(
            func.count().label('mammoth_total_ru'),
            func.sum(Profit.amount).label('profits_sum_ru'),
            func.sum(Profit.income_share).label('today_earnings_ru'),
        ).where(
            and_(Profit.user_id == self.id, Profit.timestamp == today, Profit.currency_id == Currencies.RUB.id)
        ))

        mammoth_total_ru, profits_sum_ru, today_earnings_ru = results.scalar() or (0, 0, 0)

        # Repeat for BYN currency...
        results_byn = await session.execute(select(
            func.count().label('mammoth_total_by'),
            func.sum(Profit.amount).label('profits_sum_by'),
            func.sum(Profit.income_share).label('today_earnings_by'),
        ).where(
            and_(Profit.user_id == self.id, Profit.timestamp == today, Profit.currency_id == Currencies.BYN.id)
        ))

        mammoth_total_by, profits_sum_by, today_earnings_by = results_byn.scalar() or (0, 0, 0)

        return UserTodayStatistics(
            mammoth_total_ru=mammoth_total_ru,
            profits_sum_ru=profits_sum_ru,
            today_earnings_ru=today_earnings_ru,
            mammoth_total_by=mammoth_total_by,
            profits_sum_by=profits_sum_by,
            today_earnings_by=today_earnings_by,
        )

    async def _get_total_stats(self, session: AsyncSession) -> UserTotalStatistics:
        results = await session.execute(select(
            func.count().label('mammoth_total_ru'),
            func.sum(Profit.amount).label('profits_sum_ru'),
            func.avg(Profit.income_share).label('day_earn_average_ru'),
        ).where(
            and_(Profit.user_id == self.id, Profit.currency_id == Currencies.RUB.id)
        ))

        mammoth_total_ru, profits_sum_ru, day_earn_average_ru = results.scalar() or (0, 0, 0)

        # Repeat for BYN currency...
        results_byn = await session.execute(select(
            func.count().label('mammoth_total_by'),
            func.sum(Profit.amount).label('profits_sum_by'),
            func.avg(Profit.income_share).label('day_earn_average_by'),
        ).where(
            and_(Profit.user_id == self.id, Profit.currency_id == Currencies.BYN.id)
        ))

        mammoth_total_by, profits_sum_by, day_earn_average_by = results_byn.scalar() or (0, 0, 0)

        return UserTotalStatistics(
            mammoth_total_ru=mammoth_total_ru,
            profits_sum_ru=profits_sum_ru,
            day_earn_average_ru=day_earn_average_ru,
            mammoth_total_by=mammoth_total_by,
            profits_sum_by=profits_sum_by,
            day_earn_average_by=day_earn_average_by,
        )

    async def get_status(self, session: AsyncSession) -> int:
        await session.refresh(self._user_instance, ["status"])
        return self._user_instance.status

    async def get_role(self, session: AsyncSession) -> UserRole:
        await session.refresh(self._user_instance, ["role_id"])
        return self._user_instance.role

    async def set_status(self, session: AsyncSession, status: int):
        if status not in UserStatus.ALL:
            raise InvalidStatus(self.id)

        self._user_instance.status = status
        await session.commit()

    async def set_role(self, session: AsyncSession, role_id: int):
        if role_id not in UserRole.ID_LIST:
            raise InvalidRole(self.id)

        self._user_instance.role_id = role_id
        await session.commit()

    async def set_tag(self, session: AsyncSession, tag: str):
        self._user_instance.tag = tag
        await session.commit()


class ProfitController(UserBase):
    def __init__(self, user_instance: User):
        self._user_instance = user_instance

    async def get_count(self, session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).where(Profit.user_id == self._user_instance.id))
        return result.scalar() or 0

    async def get_total(self, session: AsyncSession) -> int:
        result = await session.execute(select(func.sum(Profit.amount)).where(Profit.user_id == self._user_instance.id))
        return result.scalar() or 0


class InviteCodeController:
    def __init__(self, user_instance: User):
        self._user_instance = user_instance

    async def get_max_count(self, session: AsyncSession) -> int:
        return (await self._user_instance.group).code_limit

    async def get_count(self, session: AsyncSession) -> int:
        return await session.execute(select(func.count()).where(UserCode.user_id == self._user_instance.id))

    async def get(self, session: AsyncSession, code_id: int) -> Optional[UserCode]:
        return await session.execute(select(UserCode).where(UserCode.id == code_id)).scalar()

    async def add(self, session: AsyncSession, name: str, domain_config: dict | None):
        code_limit = await self.get_max_count(session)

        if await self.get_count(session) == code_limit:
            raise CodeLimitReached

        await session.execute(UserCode.__table__.insert().values(name=name.lower(), user_id=self._user_instance.id, domain_config=domain_config or {}))
        await session.commit()

    async def remove(self, session: AsyncSession, code_id: int):
        code = await self.get(session, code_id)
        if code is None:
            raise CodeNotExists
        await session.execute(UserCode.__table__.delete().where(UserCode.id == code_id))
        await session.commit()

    @classmethod
    async def is_exists(cls, session: AsyncSession, name: str) -> bool:
        return await session.execute(select(UserCode).where(UserCode.name == name.lower())).scalar() is not None
