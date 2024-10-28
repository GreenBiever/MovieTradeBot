from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, delete
from databases.models import User, UserCode as RefCodeORMModel
from .exceptions import RefCodeAlreadyExists
from databases.fields.json import JsonFieldUpdater


class WebsiteConfigUpdater(JsonFieldUpdater):

    @property
    def full_config(self) -> dict:
        return self._db_instance.domain_config


class RefCode:

    def __init__(self, ref_code_db_instance: RefCodeORMModel):
        self._ref_code_db_instance = ref_code_db_instance

    @classmethod
    async def create(cls, session: AsyncSession, name: str, user_id: int, domain_config: dict) -> 'RefCode':
        # Получаем пользователя и проверяем лимит кода
        user = await session.get(User, user_id)
        if user is None:
            raise ValueError(f"User with id {user_id} not found.")

        # Получаем текущее количество кодов для пользователя
        code_count = await cls.get_count_for_user(session, user_id)

        # Проверяем, достигнут ли лимит кодов
        # if code_count >= user.code_limit:  # Предположим, что у вас есть свойство code_limit у User
        #     raise Exception(f"User {user_id} has reached the code limit.")

        if await cls.is_code_with_name_exists(session, name):
            raise RefCodeAlreadyExists(name)

        # Создаем код
        new_ref_code = RefCodeORMModel(name=name.lower(), user_id=user.id, domain_config=domain_config or {})
        session.add(new_ref_code)

        try:
            await session.commit()
            await session.refresh(new_ref_code)  # Обновляем новый объект
        except IntegrityError:
            await session.rollback()
            raise RefCodeAlreadyExists(name)

        return cls(new_ref_code)

    @classmethod
    def from_db_instance(cls, ref_code_db_instance: RefCodeORMModel) -> 'RefCode':
        return cls(ref_code_db_instance)

    @classmethod
    async def get_count_for_user(cls, session: AsyncSession, user_id: int) -> int:
        result = await session.execute(select(func.count()).where(RefCodeORMModel.user_id == user_id))
        return result.scalar()

    @classmethod
    async def is_code_with_name_exists(cls, session: AsyncSession, name: str) -> bool:
        result = await session.execute(select(RefCodeORMModel).where(RefCodeORMModel.name == name))
        return result.scalar() is not None

    @classmethod
    async def bulk_delete(cls, session: AsyncSession, ids: List[int]):
        await session.execute(delete(RefCodeORMModel).where(RefCodeORMModel.id.in_(ids)))
        await session.commit()

    @property
    def id(self) -> int:
        return self._ref_code_db_instance.id

    @property
    def name(self) -> str:
        return self._ref_code_db_instance.name

    @property
    def domain_config(self) -> dict:
        return self._ref_code_db_instance.domain_config

    async def delete(self, session: AsyncSession):
        await session.delete(self._ref_code_db_instance)
        await session.commit()
