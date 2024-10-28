from typing import Union, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.models import User, UserRoles


class UserRole:

    def __init__(self, user_role_instance: UserRoles):
        self._user_role_instance = user_role_instance

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List['UserRole']:
        result = await session.execute(select(UserRoles))
        return [cls(role) for role in result.scalars().all()]

    @classmethod
    def from_db_instance(cls, user_role_instance: UserRoles) -> 'UserRole':
        return cls(user_role_instance)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, role_id: int) -> Optional['UserRole']:
        result = await session.execute(select(UserRoles).filter(UserRoles.id == role_id))
        user_role = result.scalar_one_or_none()
        return cls.from_db_instance(user_role) if user_role else None

    @property
    def id(self) -> int:
        return self._user_role_instance.id

    @property
    def name(self) -> str:
        return self._user_role_instance.name

    @classmethod
    async def assign_role_to_user(cls, session: AsyncSession, user_id: int, role_id: int) -> bool:
        user = await session.get(User, user_id)
        if user:
            user.role_id = role_id
            await session.commit()
            return True
        return False

    async def set_name(self, session: AsyncSession, name: str):
        self._user_role_instance.name = name
        await session.commit()

    async def assign_to_user(self, session: AsyncSession, user_id: int):
        user = await session.get(User, user_id)
        if user:
            user.role_id = self.id
            await session.commit()

    def __str__(self):
        return f"UserRole(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
