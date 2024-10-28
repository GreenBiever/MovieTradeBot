from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.models import User as UserORMModel
from databases.models import UserGroup as UserGroupORMModel


class UserGroup:

    """
    User group data model
    """

    def __init__(self, user_group_orm_obj: UserGroupORMModel):
        self._user_group_orm_obj = user_group_orm_obj

    @classmethod
    async def create(cls, session: AsyncSession, name: str, percent_bonus: float, code_limit: int) -> 'UserGroup':
        user_group_orm_obj = UserGroupORMModel(name=name, percent_bonus=percent_bonus, code_limit=code_limit)
        session.add(user_group_orm_obj)
        await session.commit()
        return cls(user_group_orm_obj)

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List['UserGroup']:
        result = await session.execute(select(UserGroupORMModel))
        return [cls(row[0]) for row in result.all()]

    @classmethod
    def from_db_instance(cls, user_group_orm_obj: UserGroupORMModel) -> 'UserGroup':
        return cls(user_group_orm_obj)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, group_id: int) -> Optional['UserGroup']:
        result = await session.execute(select(UserGroupORMModel).where(UserGroupORMModel.id == group_id))
        user_group = result.scalar_one_or_none()
        return cls.from_db_instance(user_group) if user_group else None

    @property
    def id(self) -> int:
        return self._user_group_orm_obj.id

    @property
    def name(self) -> str:
        return self._user_group_orm_obj.name

    @property
    def percent_bonus(self) -> float:
        return self._user_group_orm_obj.percent_bonus

    @property
    def ref_code_limit(self) -> int:
        return self._user_group_orm_obj.code_limit

    async def assign_to_user(self, session: AsyncSession, user_id: int):
        result = await session.execute(select(UserORMModel).where(UserORMModel.id == user_id))
        user_orm_obj = result.scalar_one_or_none()
        if user_orm_obj:
            user_orm_obj.group_id = self.id
            session.add(user_orm_obj)
            await session.commit()

    async def set_name(self, session: AsyncSession, name: str):
        self._user_group_orm_obj.name = name
        await session.commit()

    async def set_percent_bonus(self, session: AsyncSession, bonus: float):
        self._user_group_orm_obj.percent_bonus = bonus
        await session.commit()

    async def set_ref_code_limit(self, session: AsyncSession, limit: int):
        self._user_group_orm_obj.code_limit = limit
        await session.commit()

    def __str__(self):
        return f"UserGroup(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
