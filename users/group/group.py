from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.models import UserGroup as UserGroupDbModel
from databases.models import User as UserORMModel


class UserGroup:

    def __init__(self, user_group_db_instance: UserGroupDbModel):
        self._user_group_db_instance = user_group_db_instance

    @property
    def id(self) -> int:
        return self._user_group_db_instance.id

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List['UserGroup']:
        result = await session.execute(select(UserGroupDbModel))
        return [cls(row[0]) for row in result.all()]

    @classmethod
    async def create(cls, session: AsyncSession, name: str, percent_bonus: float, code_limit: int) -> 'UserGroup':
        user_group_db_instance = UserGroupDbModel(name=name, percent_bonus=percent_bonus, code_limit=code_limit)
        session.add(user_group_db_instance)
        await session.commit()
        return cls(user_group_db_instance)

    @classmethod
    def from_db_instance(cls, user_group_db_instance: UserGroupDbModel) -> 'UserGroup':
        return cls(user_group_db_instance)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, group_id: int) -> Optional['UserGroup']:
        result = await session.execute(select(UserGroupDbModel).where(UserGroupDbModel.id == group_id))
        user_group = result.scalar_one_or_none()
        return cls.from_db_instance(user_group) if user_group else None

    @classmethod
    async def assign_group_to_user(cls, session: AsyncSession, user_id: int, group: 'UserGroup'):
        await group.assign_to_user(session, user_id)

    @classmethod
    async def assign_group_id_to_user(cls, session: AsyncSession, user_id: int, group_id: int):
        user_group = await cls.get_by_id(session, group_id)
        if user_group:
            await user_group.assign_to_user(session, user_id)

    @property
    def name(self) -> str:
        return self._user_group_db_instance.name

    @property
    def percent_bonus(self) -> float:
        return self._user_group_db_instance.percent_bonus

    @property
    def ref_code_limit(self) -> int:
        return self._user_group_db_instance.code_limit

    async def set_name(self, session: AsyncSession, name: str):
        self._user_group_db_instance.name = name
        await session.commit()

    async def set_percent_bonus(self, session: AsyncSession, bonus: float):
        self._user_group_db_instance.percent_bonus = bonus
        await session.commit()

    async def set_ref_code_limit(self, session: AsyncSession, limit: int):
        self._user_group_db_instance.code_limit = limit
        await session.commit()

    async def assign_to_user(self, session: AsyncSession, user_id: int):
        # Здесь предполагается, что у вас есть метод для получения пользователя по ID.
        user_orm_instance = await session.execute(select(UserORMModel).where(UserORMModel.id == user_id))
        user = user_orm_instance.scalar_one_or_none()
        if user:
            user.group_id = self.id
            session.add(user)
            await session.commit()

    def __str__(self):
        return f"UserGroup(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
