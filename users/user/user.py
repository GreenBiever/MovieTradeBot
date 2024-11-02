import abc
import datetime
from typing import TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession

from users.user.traffic_source import TrafficSource
from .exceptions import TagChangeNotAllowed
from .models.user import User as UserDbModel
from .status import UserStatus, UserStatuses
from ..group.default import UserGroups
from ..group.group import UserGroup
from ..role.role import UserRole
from ..ref_code.ref_code import RefCode


class UserBase:
    pass


UserT = TypeVar('UserT', bound=UserBase)


class UserDefault(UserBase):

    def __init__(self, user_db_instance: UserDbModel):
        if not isinstance(user_db_instance, UserDbModel):
            raise ValueError(
                f'User class constructor requires UserDbModel, '
                f'not {user_db_instance.__class__.__name__}'
            )
        self._user_db_instance = user_db_instance

    @classmethod
    async def create(cls, session: AsyncSession, user_id: int, username: str, inviter_user_id: int = None) -> 'UserT':
        user_db_instance = await UserDbModel.create(session, user_id, username, inviter_user_id)
        return cls.from_db_instance(user_db_instance)

    @classmethod
    @abc.abstractmethod
    def from_db_instance(cls, user_db_instance: UserDbModel) -> 'UserT':
        pass


class User(UserDefault):

    @classmethod
    async def is_exists(cls, session: AsyncSession, user_id: int) -> bool:
        return await UserDbModel.is_exists(session, user_id)

    @classmethod
    async def is_tag_exists(cls, session: AsyncSession, tag: str) -> bool:
        return await UserDbModel.is_tag_exists(session, tag.lower())

    @classmethod
    def from_db_instance(cls, user_db_instance: UserDbModel | None) -> 'User':
        return cls(user_db_instance) if user_db_instance is not None else None

    @classmethod
    async def bulk_delete(cls, session: AsyncSession, *users: 'User'):
        await UserDbModel.bulk_delete(session, *(u.id for u in users))

    @property
    def id(self) -> int:
        return self._user_db_instance.id

    @property
    def tag(self) -> str:
        return self._user_db_instance.tag

    @property
    def status(self) -> UserStatus:
        return UserStatuses.from_id(self.status_id)

    @property
    def status_id(self) -> int:
        return self._user_db_instance.status_id

    @property
    def username(self) -> str:
        return self._user_db_instance.username

    async def get_invited_users_count(self, session: AsyncSession) -> int:
        return await self._user_db_instance.get_invited_users_count(session)

    async def get_referrer(self, session: AsyncSession) -> Union['User', None]:
        return self.__class__.from_db_instance(await UserDbModel.get_by_id(session, self._user_db_instance.referrer_id))

    async def set_referrer(self, session: AsyncSession, referrer: 'User'):
        await self._user_db_instance.set_referrer_user_id(session, referrer.id)

    async def set_traffic_source(self, session: AsyncSession, traffic_source: TrafficSource | None):
        await self._user_db_instance.set_traffic_source_id(session, traffic_source.id if traffic_source else None)

    @property
    def text_id(self) -> str:
        return "#" + self.tag if self.tag else f"@{self.username}"

    @property
    def notify_enabled(self) -> bool:
        return self._user_db_instance.notify_enabled

    @property
    def join_date(self) -> datetime.datetime:
        return self._user_db_instance.join_date

    @property
    def days_in_team(self) -> int:
        time_diff = datetime.datetime.now(tz=datetime.timezone.utc) - self.join_date
        return time_diff.days if time_diff.days > 0 else 0

    @property
    def percent_bonus(self) -> float:
        return self._user_db_instance.percent_bonus

    async def set_tag(self, session: AsyncSession, tag: str | None):
        tag_exclude_groups = (UserGroups.NEWBIE.id,)
        user_group = await self.get_group(session)
        if user_group.id in tag_exclude_groups:
            raise TagChangeNotAllowed(self)

        await self._user_db_instance.set_tag(session, tag)

    async def set_status(self, session: AsyncSession, status: UserStatus):
        await self._user_db_instance.set_status_id(session, status.id)

    async def set_join_date(self, session: AsyncSession, new_join_date: datetime.date):
        await self._user_db_instance.set_join_date(session, new_join_date)

    async def get_role(self, session: AsyncSession) -> UserRole:
        return await UserRole.get_by_id(session, await self._user_db_instance.get_role_id(session))

    async def set_role(self, session: AsyncSession, role: UserRole):
        await role.assign_to_user(session, self.id)

    async def get_group(self, session: AsyncSession) -> UserGroup:
        return await UserGroup.get_by_id(session, await self._user_db_instance.get_group_id(session))

    async def set_group(self, session: AsyncSession, group: UserGroup):
        await group.assign_to_user(session, self.id)

    async def get_group_name(self, session: AsyncSession) -> str:
        return (await self.get_group(session)).name

    async def set_username(self, session: AsyncSession, username: str | None):
        await self._user_db_instance.set_username(session, username)

    async def set_percent_bonus(self, session: AsyncSession, bonus: float):
        await self._user_db_instance.set_percent_bonus(session, bonus)

    async def toggle_notify(self, session: AsyncSession):
        await self._user_db_instance.set_notify_enabled(session, not self._user_db_instance.notify_enabled)

    class _UserRefCodes:
        def __init__(self, user: 'User'):
            self._user = user

        async def get_limit(self, session: AsyncSession) -> int:
            user_group = await self._user.get_group(session)
            return user_group.ref_code_limit

        async def get_count(self, session: AsyncSession) -> int:
            return await RefCode.get_count_for_user(session, self._user.id)

        async def add(self, session: AsyncSession, name: str) -> RefCode:
            name = name.lower()
            return await RefCode.create(session, name, self._user.id)

    @property
    def ref_codes(self) -> _UserRefCodes:
        return self._UserRefCodes(self)

    class _Telegram:
        async def send_private_message(self, text: str, parse_mode: str = 'HTML'):
            pass

    def __str__(self) -> str:
        return f'User(\n\t' \
               f'id={self.id},\n\t' \
               f'username={self.username},\n\t' \
               f'tag={self.tag},\n\t' \
               f'notify_enabled={self.notify_enabled}\n\t' \
               f'days_in_team={self.days_in_team}\n' \
               f')'

    def __repr__(self):
        return self.__str__()
