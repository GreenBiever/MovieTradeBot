from typing import List, Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from databases.models import User, UserCode, Hosting_Website, UserCodeType
from databases.enums import CurrencyEnum
from aiogram import Bot
from keyboards import keyboard


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalars().first()


async def register_referal(session: AsyncSession, referer: User, user: User, bot: Bot):
    (await referer.awaitable_attrs.referals).append(user)
    if referer.status == 2:
        await bot.send_message(
            referer.tg_id,
            f'Ваш реферал {user.tg_id} привязан к вашей учетной записи. '
        )


async def get_promocodes_by_user(session: AsyncSession, tg_id: int) -> Sequence:
    result = await session.execute(select(UserCode).where(UserCode.user_id == tg_id))
    return result.scalars().all()


async def get_promocode_by_id(session: AsyncSession, id: int) -> UserCode | None:
    result = await session.execute(select(UserCode).where(UserCode.id == id))
    return result.scalars().first()


async def get_websites(session: AsyncSession) -> Sequence:
    result = await session.execute(select(Hosting_Website))
    return result.scalars().all()


async def get_promocode_types(session: AsyncSession) -> Sequence:
    result = await session.execute(select(UserCodeType))
    return result.scalars().all()