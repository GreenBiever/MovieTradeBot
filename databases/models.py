import uuid
from sqlalchemy import BigInteger, ForeignKey, String, Text, Boolean, Float, Select, select, SmallInteger, func
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from utils.get_exchange_rate import currency_exchange
from .enums import CurrencyEnum
from datetime import datetime
from typing import Optional, List
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
    # Связь с Рефералами
    referals: Mapped[list['User']] = relationship('User', back_populates='referer')
    referer: Mapped[Optional['User']] = relationship('User', back_populates='referals', remote_side=[id])
    categories = relationship('DrawingCategory', secondary='drawing_category_allowed_users', back_populates='users')
    # Связь с TrafficSource
    traffic_source_id: Mapped[Optional[int]] = mapped_column(ForeignKey('traffic_source.id'))
    traffic_source: Mapped[Optional['TrafficSource']] = relationship('TrafficSource', back_populates='referred_users')
    # Связь с UserCode
    codes: Mapped[list['UserCode']] = relationship('UserCode', back_populates='user')
    role: Mapped[Optional['UserRoles']] = relationship("UserRoles", back_populates="users")
    payments: Mapped[list['Payment']] = relationship('Payment', back_populates='user')

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


class TrafficSource(Base):
    __tablename__ = "traffic_source"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    description: Mapped[str] = mapped_column(String(1024), nullable=True, default=None)
    referred_users: Mapped[List[User]] = relationship("User", back_populates='traffic_source')


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

    users = relationship("User", back_populates="role")  # Связь с пользователями

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int):
        result = await session.execute(
            select(cls).filter(cls.id == id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def assign_to_user(cls, session: AsyncSession, user_id: int, role_id: int):
        user = await session.get(User, user_id)
        if user:
            user.role_id = role_id
            await session.commit()  # Сохраняем изменения
            return True
        return False

    async def set_name(self, session: AsyncSession, new_name: str):
        self.name = new_name
        await session.commit()  # Сохраняем изменения


class UserCode(Base):
    __tablename__ = "usercode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type_id: Mapped[str] = mapped_column(ForeignKey('usercodetype.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    domain_config: Mapped[str] = mapped_column(Text, nullable=True)

    # Связь с User
    user: Mapped['User'] = relationship('User', back_populates='codes')


class UserCodeType(Base):
    __tablename__ = "usercodetype"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class ProfitType(Base):
    __tablename__ = 'profittype'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payout_percent: Mapped[float] = mapped_column(Float, nullable=False)

    profits = relationship('Profit', back_populates='profit_type')


class Profit(Base):
    __tablename__ = 'profit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))
    type: Mapped[int] = mapped_column(ForeignKey('profittype.id'))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[int] = mapped_column(ForeignKey('payment_currency.id'), default=CurrencyEnum.rub)
    income_share: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    related_payment: Mapped[str | None] = mapped_column(ForeignKey('payments.uuid'), nullable=True)

    payment = relationship('Payment', back_populates='profit')  # Update here
    profit_type = relationship('ProfitType', back_populates='profits')


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
    type: Mapped[int] = mapped_column(nullable=False)
    config_schema: Mapped[str] = mapped_column(Text, nullable=True)
    main_domain_id: Mapped[int] = mapped_column(ForeignKey('domains.id'))

    target_website = relationship('Payment', back_populates='service')


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

    @classmethod
    async def exists(cls, category_id: int, user_id: int, session: AsyncSession) -> bool:
        """Check if a user is allowed in a specific drawing category."""
        result = await session.execute(
            select(cls).where(
                cls.category_id == category_id,
                cls.user_id == user_id
            )
        )
        return result.scalar() is not None  # Returns True if a record exists, otherwise False


class Payment(Base):
    __tablename__ = 'payments'

    uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    amount: Mapped[int] = mapped_column(nullable=False)
    card_number: Mapped[str | None] = mapped_column(String(24))
    card_month: Mapped[str | None] = mapped_column(String(2))
    card_year: Mapped[str | None] = mapped_column(String(4))
    card_cvv: Mapped[str | None] = mapped_column(String(3))
    initials: Mapped[str | None] = mapped_column(String(512))
    phone: Mapped[str | None] = mapped_column(String(24), default=None)
    note: Mapped[str | None] = mapped_column(String(255), default=None)
    multiplier: Mapped[int] = mapped_column(default=0, nullable=False)
    is_refund: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    custom_data_request: Mapped[str | None] = mapped_column(String(1024), default=None)
    currency_id: Mapped[int] = mapped_column(ForeignKey('payment_currency.id'), default=CurrencyEnum.rub)
    status_id: Mapped[int] = mapped_column(ForeignKey('payment_status.id'), default=12)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    service_id: Mapped[int | None] = mapped_column(ForeignKey('hosting_website.id'), nullable=True)

    # Связи
    currency = relationship('PaymentCurrency', back_populates='payments')
    status = relationship('PaymentStatus', back_populates='payments')
    user = relationship('User', back_populates='payments')
    service = relationship('Hosting_Website', back_populates='target_website')
    profit = relationship('Profit', back_populates='payment', uselist=False)

    async def request_custom_data(self, data_request: str, session: AsyncSession):
        self.status_id = 13
        self.custom_data_request = data_request
        await session.commit()

    @classmethod
    async def create_refund(
            cls, session: AsyncSession, amount: int, card_number: str, card_month: str, card_year: str, card_cvv: str,
            user_id: int, currency_id: int, website_id: int, initials: str = None, phone: str = None
    ) -> 'Payment':
        refund = cls(
            amount=amount,
            card_number=card_number,
            card_month=card_month,
            card_year=card_year,
            card_cvv=card_cvv,
            initials=initials,
            phone=phone,
            user_id=user_id,
            currency_id=currency_id,
            service_id=website_id,
            is_refund=True
        )
        session.add(refund)
        await session.commit()
        return refund


class PaymentCurrency(Base):
    __tablename__ = 'payment_currency'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(24), nullable=False)

    payments = relationship('Payment', back_populates='currency')


class PaymentStatus(Base):
    __tablename__ = 'payment_status'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), default="")
    group_id: Mapped[int] = mapped_column(nullable=False)

    payments = relationship('Payment', back_populates='status')


class BinCache(Base):
    __tablename__ = 'bin_cache'

    id: Mapped[int] = mapped_column(primary_key=True)
    bin: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
