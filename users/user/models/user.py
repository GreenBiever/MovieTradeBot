import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import Session
from typing import Optional

class User:

    def __init__(self, user_orm_obj):
        self._user_orm_obj = user_orm_obj

    @classmethod
    async def is_exists(cls, session: AsyncSession, user_id: int) -> bool:
        result = await session.execute(select(User).filter_by(id=user_id))
        return result.scalars().first() is not None

    @classmethod
    async def is_tag_exists(cls, session: AsyncSession, tag: str) -> bool:
        result = await session.execute(select(User).filter_by(tag=tag))
        return result.scalars().first() is not None


    @classmethod
    def from_db_instance(cls, user_orm_obj) -> Optional['User']:
        return cls(user_orm_obj) if user_orm_obj is not None else None

    @classmethod
    async def bulk_delete(cls, session: AsyncSession, *ids: int):
        await session.execute(delete(User).filter(User.id.in_(ids)))
        await session.commit()

    @property
    def id(self) -> int:
        return self._user_orm_obj.id

    @property
    def tag(self) -> Optional[str]:
        return self._user_orm_obj.tag

    @property
    def status_id(self) -> int:
        return self._user_orm_obj.status

    @property
    def username(self) -> Optional[str]:
        return self._user_orm_obj.username

    @property
    def referrer_id(self) -> Optional[int]:
        return self._user_orm_obj.referrer_id

    @property
    def notify_enabled(self) -> bool:
        return bool(self._user_orm_obj.notifications)

    @property
    def join_date(self) -> datetime.datetime:
        return self._user_orm_obj.join_date

    @property
    def percent_bonus(self) -> float:
        return self._user_orm_obj.percent_bonus

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: int) -> Optional['User']:
        result = await session.execute(select(User).filter_by(id=user_id))
        user_orm_obj = result.scalars().first()
        return cls.from_db_instance(user_orm_obj)

    async def get_invited_users_count(self, session: AsyncSession) -> int:
        result = await session.execute(select(User).filter_by(referrer_id=self.id))
        return result.scalars().count()

    async def set_referrer_user_id(self, session: AsyncSession, referrer_id: int):
        self._user_orm_obj.referrer_id = referrer_id
        await session.commit()

    async def set_percent_bonus(self, session: AsyncSession, bonus: float):
        self._user_orm_obj.percent_bonus = bonus
        await session.commit()

    async def get_role_id(self, session: AsyncSession) -> Optional[int]:
        await session.refresh(self._user_orm_obj)
        return self._user_orm_obj.role_id

    async def get_group_id(self, session: AsyncSession) -> Optional[int]:
        await session.refresh(self._user_orm_obj)
        return self._user_orm_obj.group_id

    async def set_tag(self, session: AsyncSession, tag: Optional[str]):
        self._user_orm_obj.tag = tag
        await session.commit()

    async def set_status_id(self, session: AsyncSession, status_id: int):
        self._user_orm_obj.status = status_id
        await session.commit()

    async def set_join_date(self, session: AsyncSession, new_join_date: datetime.date):
        self._user_orm_obj.join_date = new_join_date
        await session.commit()

    async def set_username(self, session: AsyncSession, username: Optional[str]):
        self._user_orm_obj.username = username
        await session.commit()

    async def set_notify_enabled(self, session: AsyncSession, enabled: bool):
        self._user_orm_obj.notifications = enabled
        await session.commit()

    async def set_traffic_source_id(self, session: AsyncSession, traffic_source_id: int):
        self._user_orm_obj.traffic_source_id = traffic_source_id
        await session.commit()
