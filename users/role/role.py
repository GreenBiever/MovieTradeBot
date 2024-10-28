from typing import Union
from databases.models import UserRoles as UserRoleDbModel
from sqlalchemy.ext.asyncio import AsyncSession


class UserRole:
    """
    User role data model
    """

    def __init__(self, user_role_db_instance: UserRoleDbModel):
        self._user_role_db_instance = user_role_db_instance

    @classmethod
    async def get_all(cls, session: AsyncSession) -> list['UserRole']:
        roles = await UserRoleDbModel.get_all(session)  # Передаем session
        return [cls.from_db_instance(role) for role in roles]

    @classmethod
    def from_db_instance(cls, user_role_db_instance: UserRoleDbModel) -> 'UserRole':
        return cls(user_role_db_instance)

    @classmethod
    async def get_by_id(cls, session: AsyncSession, role_id: int) -> Union['UserRole', None]:
        role_db_instance = await UserRoleDbModel.get_by_id(session, role_id)  # Передаем session
        return cls.from_db_instance(role_db_instance) if role_db_instance else None

    @classmethod
    async def assign_role_to_user(cls, session: AsyncSession, user_id: int, role: 'UserRole'):
        await role.assign_to_user(session, user_id)  # Передаем session

    @classmethod
    async def assign_role_id_to_user(cls, session: AsyncSession, user_id: int, role_id: int):
        user_role = await cls.get_by_id(session, role_id)  # Передаем session
        if user_role:
            await user_role.assign_to_user(session, user_id)

    @property
    def id(self) -> int:
        return self._user_role_db_instance.id

    @property
    def name(self) -> str:
        return self._user_role_db_instance.name

    async def assign_to_user(self, session: AsyncSession, user_id: int, role_id: int):
        await self._user_role_db_instance.assign_to_user(session, user_id, role_id)  # Передаем session

    async def set_name(self, session: AsyncSession, name: str):
        await self._user_role_db_instance.set_name(session, name)  # Передаем session

    def __str__(self):
        return f"UserRole(id={self.id}, name='{self.name}')"

    def __repr__(self):
        return self.__str__()
