from datetime import datetime
from typing import Optional

from aiogram import Bot

import config
from databases.connect import get_session
from databases.crud import get_user_by_tg_id, get_promocodes_by_user, get_promocode_by_id, get_websites, get_promocode_types
from fastapi import APIRouter, Query, Request, Path, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from databases.models import User, UserGroup, UserRoles, UserCode, Hosting_Website, UserCodeType
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


class PromocodeView(BaseModel):
    name: str
    user_id: int
    type_id: int


async def get_user_avatar(tg_id: int):
    photos = await bot.get_user_profile_photos(tg_id, limit=1)
    print(photos)

    if photos.total_count > 0:
        # Берем первую фотографию из результата
        file_id = photos.photos[0][0].file_id
        # Получаем файл по ID
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # Формируем URL для скачивания
        avatar_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
        print(avatar_url)
        return avatar_url


# api methods for index.html page


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
    role = await user.get_role(session)
    user_view.role_id = role.name if role else None
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


@router.post("/user/{tg_id}/tag", response_class=HTMLResponse)
async def update_tag(request: Request,
                     tg_id: int = Path(...),
                     session: AsyncSession = Depends(get_session)):
    data = await request.json()
    new_tag = data.get("new_tag")
    user = await get_user_by_tg_id(session, tg_id)
    user.tag = new_tag
    await session.commit()
    return f"Tag updated to {new_tag} for user {tg_id}"


# api methods for promocode.html page

@router.get("/promocode.html/", response_class=HTMLResponse)
async def get_promocode_page(request: Request, id: str = Query()):
    if not id:
        raise HTTPException(status_code=400, detail="ID не передан")
    return templates.TemplateResponse(
        name="promocode.html", context={"request": request, "id": id}
    )


@router.get("/promocodes/{tg_id}", response_class=JSONResponse)
async def get_promocodes(request: Request, tg_id: int = Path(...), session: AsyncSession = Depends(get_session)):
    promocodes = await get_promocodes_by_user(session, tg_id)

    # Формируем список промокодов
    promocode_list = []
    if promocodes:
        for promocode in promocodes:
            promocode_list.append({
                'id': promocode.id,
                'name': promocode.name,
            })

    # Возвращаем в формате JSON
    return {'promocodes': promocode_list}


@router.get("/websiteList", response_class=JSONResponse)
async def get_all_websites(session: AsyncSession = Depends(get_session)):
    websites = await get_websites(session)
    website_list = [{'id': website.id, 'name': website.name} for website in websites]
    return {'websites': website_list}


@router.get("/promocodeTypes", response_class=JSONResponse)
async def fetch_promocode_types(session: AsyncSession = Depends(get_session)):
    promocode_types = await get_promocode_types(session)
    promocodes_list = [{'id': type.id, 'name': type.name} for type in promocode_types]
    return {'promocode_types': promocodes_list}


@router.get("/promocode/{code_id}", response_class=JSONResponse)
async def get_promocode(request: Request, code_id: int = Path(...), session: AsyncSession = Depends(get_session)):
    promocode = await get_promocode_by_id(session, code_id)


@router.post("/promocodeCreate/{user_id}", response_class=JSONResponse)
async def create_promocode(request: Request, user_id: int = Path(...), session: AsyncSession = Depends(get_session)):
    data = await request.json()
    name = data.get("name")
    type_id = data.get("type_id")
    await session.execute(insert(UserCode).values(
        name=name,
        user_id=user_id,
        type_id=type_id
    ))
    await session.commit()
    return {"message": "Promocode created successfully"}