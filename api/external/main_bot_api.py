from datetime import datetime
from typing import Optional

from aiogram import Bot

import config
from databases.connect import get_session
from databases.crud import get_user_by_tg_id
from fastapi import APIRouter, Query, Request, Path, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from databases.models import User, UserGroup, UserRoles
from pydantic import BaseModel

bot: Bot = Bot(config.BOT_TOKEN)
router = APIRouter()
templates = Jinja2Templates(directory="webapp")


class UserView(BaseModel):
    tg_id: int
    tag: str | None
    username: str | None
    balance: float
    currency: str
    payment_notifications: bool
    navigation_notifications: bool
    group_id: str | None
    role_id: str | None
    join_day: Optional[int] = None
    is_verified: bool
    percent: int
    mamonts_number: int
    avatar_url: str | None = None

    class Config:
        from_attributes = True





async def get_user_avatar(tg_id: int):
    photos = await bot.get_user_profile_photos(tg_id, limit=1)

    if photos.total_count > 0:
        # Берем первую фотографию из результата
        file_id = photos.photos[0][0].file_id
        # Получаем файл по ID
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # Формируем URL для скачивания
        avatar_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
        return avatar_url


@router.get("/", response_class=HTMLResponse)
async def get_main_page(request: Request, id: str = Query()):
    if not id:
        raise HTTPException(status_code=400, detail="ID не передан")
    return templates.TemplateResponse(
        name="index.html", context={"request": request, "id": id}
    )


@router.get("/user/{tg_id}", response_model=UserView)
async def get_user_page(
        request: Request,
        tg_id: int = Path(...),
        session: AsyncSession = Depends(get_session)
):
    # Получаем пользователя из базы данных
    user = await get_user_by_tg_id(session, tg_id)
    # Преобразуем SQLAlchemy объект в Pydantic модель
    user_view = UserView(
        tg_id=user.tg_id,
        tag=user.tag,
        username=user.username,
        balance=user.balance,
        currency=user.currency,
        payment_notifications=user.payment_notifications,
        navigation_notifications=user.navigation_notifications,
        group_id=None,  # Мы позже установим значение
        role_id=None,  # Мы позже установим значение
        join_day=None,  # Заранее присвоим пустую строку
        is_verified=user.is_verified,
        percent=0,  # Мы позже установим значение
        mamonts_number=0,  # Мы позже установим значение
        avatar_url=None  # Мы позже установим значение
    )
    # Получаем аватар пользователя
    avatar_url = await get_user_avatar(tg_id)
    user_view.avatar_url = avatar_url
    group = await user.get_group(session)
    user_view.group_id = group.name if group else None
    print(group.name)
    role = await user.get_role(session)
    user_view.role_id = role.name if role else None
    print(role.name)
    join_day = await user.get_join_day()
    user_view.join_day = join_day
    return user_view


@router.post("/user/{tg_id}/notifications", response_class=HTMLResponse)
async def toggle_notifications(request: Request,  # Перемещаем request первым
                               tg_id: int = Path(...),
                               session: AsyncSession = Depends(get_session)):
    data = await request.json()
    notification_type = data.get("notification_type")
    status = data.get("status")
    # Логика для обработки включения/выключения уведомлений
    user = await get_user_by_tg_id(session, tg_id)

    # Сохраните изменения в базе данных (измените логику по необходимости)
    if notification_type == "payment":
        user.payment_notifications = status
    elif notification_type == "navigation":
        user.navigation_notifications = status

    await session.commit()

    return f"{notification_type.capitalize()} notifications turned {'on' if status else 'off'} for user {tg_id}"
