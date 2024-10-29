from typing import List, Sequence

from sqlalchemy import select, update, insert, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from databases.models import User, UserCode, Hosting_Website, UserCodeType, Domains, ProfitType, UserGroup, UserRoles, \
    DrawingCategory
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


async def get_hosting_website(session, website_type) -> Sequence:
    result = await session.execute(select(Hosting_Website).where(Hosting_Website.type == website_type))
    host_website = result.scalars().first()
    domain = await session.execute(select(Domains.domain).where(Domains.id == host_website.main_domain_id))
    return domain.scalars().first()


async def get_promocode_by_name(session, promocode_name) -> UserCode | None:
    result = await session.execute(select(UserCode).where(UserCode.name == promocode_name))
    return result.scalars().first()


async def init_db(session: AsyncSession):
    result = await session.execute(select(Domains))
    if not result.scalars().all():
        # Если таблица пустая
        await session.execute(insert(Domains).values([
            {'id': 1, 'domain': 'antikino.com'},
            {'id': 2, 'domain': 'theatre.com'},
            {'id': 3, 'domain': 'exhibition.com'},
            {'id': 4, 'domain': 'trade.com'},
            {'id': 5, 'domain': 'blablacar.com'},
            {'id': 6, 'domain': 'payment.com'}
        ]))

    result = await session.execute(select(ProfitType))
    if not result.scalars().all():  # Если таблица пустая
        await session.execute(insert(ProfitType).values([
            {'id': 1, 'name': 'Первая оплата', 'is_unique': True, 'payout_percent': 0.6},
            {'id': 2, 'name': 'X-Оплата', 'is_unique': False, 'payout_percent': 0.5},
            {'id': 3, 'name': 'Возврат', 'is_unique': False, 'payout_percent': 0.45},
            {'id': 4, 'name': 'Прямой перевод', 'is_unique': True, 'payout_percent': 0.55},
            {'id': 5, 'name': 'Обнал', 'is_unique': False, 'payout_percent': 0.45}
        ]))

    # Проверка и вставка данных в таблицу UserCodeType
    result = await session.execute(select(UserCodeType))
    if not result.scalars().all():  # Если таблица пустая
        await session.execute(insert(UserCodeType).values([
            {'id': 1, 'name': 'Cinema'},
            {'id': 2, 'name': 'Theatre'},
            {'id': 3, 'name': 'Exhibitions'},
            {'id': 4, 'name': 'Trade'},
            {'id': 5, 'name': 'BlaBlaCar'},
            {'id': 6, 'name': 'Payment'}
        ]))

    # Проверка и вставка данных в таблицу UserGroup
    result = await session.execute(select(UserGroup))
    if not result.scalars().all():  # Если таблица пустая
        await session.execute(insert(UserGroup).values([
            {'id': 1, 'name': 'Silver', 'percent_bonus': 0, 'code_limit': 5},
            {'id': 2, 'name': 'Gold', 'percent_bonus': 0.01, 'code_limit': 10},
            {'id': 3, 'name': 'Titanium', 'percent_bonus': 0.02, 'code_limit': 7},
            {'id': 4, 'name': 'Sapphire', 'percent_bonus': 0.03, 'code_limit': 7},
            {'id': 5, 'name': 'Ruby', 'percent_bonus': 0.04, 'code_limit': 10},
            {'id': 6, 'name': 'Diamond', 'percent_bonus': 0.05, 'code_limit': 30}
        ]))

    # Проверка и вставка данных в таблицу UserRoles
    result = await session.execute(select(UserRoles))
    if not result.scalars().all():  # Если таблица пустая
        await session.execute(insert(UserRoles).values([
            {'id': 1, 'name': '🥷🏿 Воркер'},
            {'id': 2, 'name': '💳 Вбивер'},
            {'id': 3, 'name': '🤴 Админ'},
            {'id': 4, 'name': '👨‍💻 Прогер'},
            {'id': 5, 'name': '📣 Саппорт'}
        ]))

    result = await session.execute(select(DrawingCategory))
    if not result.scalars().all():  # Если таблица пустая
        await session.execute(insert(DrawingCategory).values([
            {'id': 1, 'name': '🎟 Билеты'},
            {'id': 2, 'name': '🆘 ТП'},
            {'id': 3, 'name': '🌐 Сайт'},
            {'id': 4, 'name': '🏦 Банк'}
        ]))

    result = await session.execute(select(Hosting_Website))
    if not result.scalars().all():
        # Если таблица пустая
        await session.execute(insert(Hosting_Website).values([
            {'id': 1, 'name': 'Antikino', 'type': 1, 'main_domain_id': 1},
            {'id': 2, 'name': 'Theatre', 'type': 2, 'main_domain_id': 2},
            {'id': 3, 'name': 'Exhibition', 'type': 3, 'main_domain_id': 3},
            {'id': 4, 'name': 'Trade', 'type': 4, 'main_domain_id': 4},
            {'id': 5, 'name': 'BlaBlaCar', 'type': 5, 'main_domain_id': 5},
            {'id': 6, 'name': 'Payment', 'type': 6, 'main_domain_id': 6}
        ]))

    await session.commit()  # Коммит изменений вне контекста session.begin()
