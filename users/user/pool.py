from typing import Union, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from databases.models import User as UserORMModel
from .models.user import User as UserDbModel
from .user import User


class UserPool:

    def __init__(self, limit: int = 0):
        self.limit = limit

    @classmethod
    async def get_by_id(cls, session: AsyncSession, *ids: int) -> Union[User, List[User], None]:
        if len(ids) == 1:
            user_filtered = await session.execute(
                select(UserORMModel).filter(UserORMModel.id == ids[0])
            )
            user = user_filtered.scalar_one_or_none()
            return cls._init_user_instance(user) if user else None

        users_filtered = await session.execute(
            select(UserORMModel).filter(UserORMModel.id.in_(ids))
        )
        users = users_filtered.scalars().all()
        return cls._fill_search_results_with_none(users, 'id', ids)

    @classmethod
    async def get_by_username(cls, session: AsyncSession, *usernames: str) -> Union[User, List[User], None]:
        usernames = list(map(lambda u: u.replace('@', ''), usernames))
        if len(usernames) == 1:
            user_filtered = await session.execute(
                select(UserORMModel).filter(UserORMModel.username == usernames[0])
            )
            user = user_filtered.scalar_one_or_none()
            return cls._init_user_instance(user) if user else None

        users_filtered = await session.execute(
            select(UserORMModel).filter(UserORMModel.username.in_(usernames))
        )
        users = users_filtered.scalars().all()
        return cls._fill_search_results_with_none(users, 'username', usernames)

    @classmethod
    async def get_by_ref_code(cls, session: AsyncSession, ref_code_name: str) -> Union[User, List[User], None]:
        user_filtered = await session.execute(
            select(UserORMModel).filter(UserORMModel.codes.any(name=ref_code_name.lower()))
        )
        user = user_filtered.scalar_one_or_none()
        return cls._init_user_instance(user) if user else None

    @classmethod
    def _fill_search_results_with_none(cls, users: List[User], attr_name: str, used_search_params: List[Any]) -> List[
        User]:
        user_list = []
        for search_param in used_search_params:
            try:
                user_list.append(next(u for u in users if getattr(u, attr_name) == search_param))
            except StopIteration:
                user_list.append(None)

        return user_list

    @classmethod
    async def _get_user_instances_from_orm_obj_list(cls, user_orm_obj_list: List[UserORMModel]):
        return [cls._init_user_instance(user) for user in user_orm_obj_list]

    @classmethod
    def _init_user_instance(cls, user_orm_obj: UserORMModel) -> User:
        return User.from_db_instance(UserDbModel.from_db_instance(user_orm_obj))
