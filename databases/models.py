from sqlalchemy import BigInteger, ForeignKey, String, Text, Boolean, Float, Select
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from utils.get_exchange_rate import currency_exchange
from .enums import CurrencyEnum
from datetime import datetime
from typing import Optional
from .connect import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, Table, Column, Integer
import config
from aiogram import types, Bot

engine = create_async_engine(config.Database.DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tag: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    balance: Mapped[int] = mapped_column(default=0)
    payment_notifications: Mapped[bool] = mapped_column(default=False)
    navigation_notifications: Mapped[bool] = mapped_column(default=False)
    currency: Mapped[CurrencyEnum] = mapped_column(default=CurrencyEnum.usd)
    join_date: Mapped[datetime] = mapped_column(default=datetime.now())
    group_id: Mapped[int | None] = mapped_column(ForeignKey('usergroup.id'))
    role_id: Mapped[int | None] = mapped_column(ForeignKey('userroles.id'))
    referer_id: Mapped[Optional['User']] = mapped_column(ForeignKey('users.id'))
    referals: Mapped[list['User']] = relationship('User', back_populates='referer')
    referer: Mapped[Optional['User']] = relationship('User', back_populates='referals', remote_side=[id])
    categories = relationship('DrawingCategory', secondary='drawing_category_allowed_users', back_populates='users')

    async def get_balance(self) -> float:
        '''Return user balance converted to user currency'''
        return await currency_exchange.get_exchange_rate(self.currency, self.balance)

    async def send_log(self, bot: Bot, text: str,
                       kb: types.InlineKeyboardMarkup | None = None) -> None:
        '''Send log about user actions to his referer'''
        referer = await self.awaitable_attrs.referer
        name = '@' + self.username
        ident = f'{name}(<code>{self.tg_id}</code>)' if name else self.tg_id
        if referer:
            await bot.send_message(
                referer.tg_id,
                f'''Пользователем {ident} было совершено действие:
{text}''', reply_markup=kb, parse_mode='HTML')

    async def get_group(self, session: AsyncSession):
        '''Return user group name'''
        result = await session.execute(Select(UserGroup).where(UserGroup.id == self.group_id).limit(1))
        return result.scalars().first()

    async def get_role(self, session: AsyncSession):
        '''Return user role name'''
        result = await session.execute(Select(UserRoles).where(UserRoles.id == self.role_id).limit(1))
        return result.scalars().first()

    async def get_join_day(self) -> int:
        '''Return user total days of user in the system'''
        current_date = datetime.now()
        # Разница между текущей датой и датой регистрации
        delta = current_date - self.join_date
        # Количество дней с момента регистрации
        days = delta.days
        return days

    def __str__(self):
        if self.username is not None:
            return f"@{self.username}"


class UserGroup(Base):
    __tablename__ = "usergroup"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    percent_bonus: Mapped[float] = mapped_column(default=0)
    code_limit: Mapped[int] = mapped_column(default=0)


class UserRoles(Base):
    __tablename__ = "userroles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class UserCode(Base):
    __tablename__ = "usercode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type_id: Mapped[str] = mapped_column(ForeignKey('usercodetype.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    domain_config: Mapped[str] = mapped_column(Text, nullable=True)


class UserCodeType(Base):
    __tablename__ = "usercodetype"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class ProfitType(Base):
    __tablename__ = 'profittype'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payout_percent: Mapped[float] = mapped_column(Float, nullable=False)


class Profit(Base):
    __tablename__ = 'profit'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))
    type: Mapped[int] = mapped_column(ForeignKey('profittype.id'))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(default=CurrencyEnum.rub)
    income_share: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    related_payment: Mapped[int | None] = mapped_column(ForeignKey('payment.uuid'))


class Payment(Base):
    __tablename__ = 'payment'

    uuid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(default=CurrencyEnum.rub)
    type: Mapped[int] = mapped_column(String(255), nullable=False)
    is_refund: Mapped[bool] = mapped_column(default=False)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    worker: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[bool] = mapped_column(default=False)


class Domains(Base):
    __tablename__ = 'domains'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    ssl_certificate: Mapped[str] = mapped_column(Text, nullable=True)


class Hosting_Website(Base):
    __tablename__ = 'hosting_website'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    config_key: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    config_schema: Mapped[str] = mapped_column(Text, nullable=True)
    main_domain_id: Mapped[int] = mapped_column(ForeignKey('domains.id'))


class Trade_User(Base):
    __tablename__ = "trade_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    balance: Mapped[int] = mapped_column(default=0)
    currency: Mapped[CurrencyEnum] = mapped_column(default=CurrencyEnum.rub)
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    min_withdraw: Mapped[int] = mapped_column(default=500)
    is_withdraw: Mapped[bool] = mapped_column(default=True)
    luck: Mapped[int] = mapped_column(default=50)
    referer_id: Mapped[Optional['User']] = mapped_column(ForeignKey('users.tg_id'))


class DrawingCategory(Base):
    __tablename__ = 'drawing_category'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Связь многие-ко-многим через вспомогательную таблицу
    users = relationship('User', secondary='drawing_category_allowed_users', back_populates='categories')


class DrawingCategoryAllowedUsers(Base):
    __tablename__ = 'drawing_category_allowed_users'

    category_id: Mapped[int] = mapped_column(ForeignKey('drawing_category.id'), nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'), nullable=False, primary_key=True)
