from datetime import datetime
from typing import Optional

from aiogram import Bot
import json
import config
from databases.connect import get_session
from databases.crud import get_user_by_tg_id, get_promocodes_by_user, get_promocode_by_id, get_websites, \
    get_promocode_types, get_hosting_website
from fastapi import APIRouter, Query, Request, Path, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
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
    id = promocode.id
    name = promocode.name
    type = promocode.type_id
    return {'id': id, 'name': name, 'type': type}


@router.post("/promocodeCreate/{user_id}", response_class=JSONResponse)
async def create_promocode(request: Request, user_id: int = Path(...), session: AsyncSession = Depends(get_session)):
    data = await request.json()
    name = data.get("name")
    type_id = data.get("type_id")
    domain = await get_hosting_website(session, type_id)
    settings = {}
    if type_id == "1":
        settings = {
            "country": "EU",
            "language": "EN",
            "currency": "UAH",
            "preview": {
                "pictures": {
                    "picture1": "",
                    "picture2": "",
                    "picture3": "",
                    "picture4": "",
                    "picture5": ""
                }
            },
            "rooms": [
                {"address": "Адрес комнаты 1", "price": 150},
                {"address": "Адрес комнаты 2", "price": 200},
                {"address": "Адрес комнаты 3", "price": 250},
                {"address": "Адрес комнаты 4", "price": 300},
                {"address": "Адрес комнаты 5", "price": 350}
            ],
            "time": f"{datetime.now().isoformat()}"
        }
    # Добавить логику для других типов промокодов
    elif type_id == "4":
        settings = {
            "currency": "USD",
            "language": "Английский",
            "max_withdrawal": 1000,
            "success_rate": 95,
            "worker_settings": {
                "mamont_management": True,
                "min_withdrawal": 100
            }
        }
    elif type_id == "5":
        settings = {
            "country": "Россия",
            "language": "Русский",
            "currency": "RUB",
            "seating": {
                "capacity": 80
            },
            "time": f"{datetime.now().isoformat()}"
        }

    settings_json = json.dumps(settings)  # Сериализуем настройки в JSON

    # Сохранение промокода в базу данных
    await session.execute(insert(UserCode).values(
        name=name,
        user_id=user_id,
        type_id=type_id,
        domain_config=settings_json  # Сохраняем сериализованный JSON
    ))
    await session.commit()
    return {"message": "Promocode created successfully"}


@router.get("/promocodeDelete/{code_id}", response_class=JSONResponse)
async def delete_promocode(request: Request, code_id: int = Path(...), session: AsyncSession = Depends(get_session)):
    promocode = await get_promocode_by_id(session, code_id)
    await session.delete(promocode)
    await session.commit()
    return {"message": "Promocode deleted successfully"}


# api methods for edit_promocode.html page
@router.get("/edit_promo/", response_class=HTMLResponse)
async def get_promocode_page(
        request: Request,
        id: str = Query(None, description="User ID"),
        promocodeId: str = Query(None, description="Promocode ID")
):
    if not id or not promocodeId:
        raise HTTPException(status_code=400, detail="ID or PromocodeID not provided")

    return templates.TemplateResponse(
        name="edit_promo.html",
        context={"request": request, "id": id, "promocodeId": promocodeId}
    )


@router.post("/promocodeUpdateAntikino/{code_id}", response_class=JSONResponse)
async def update_antikino_promocode(request: Request, code_id: int = Path(...),
                                    session: AsyncSession = Depends(get_session)):
    data = await request.json()

    # Извлекаем новые параметры
    country = data.get("country")
    language = data.get("language")
    currency = data.get("currency")

    # Получаем текущий промокод по user_id
    result = await session.execute(select(UserCode).where(UserCode.id == code_id))
    user_code = result.scalars().first()

    if not user_code:
        return JSONResponse(status_code=404, content={"message": "Promocode not found"})

    # Обновляем настройки промокода
    settings = json.loads(user_code.domain_config)
    settings.update({
        "country": country,
        "language": language,
        "currency": currency
    })
    user_code.domain_config = json.dumps(settings)

    # Сохраняем изменения в базе данных
    session.add(user_code)
    await session.commit()

    return {"message": "Promocode updated successfully"}


@router.post("/promocodeUpdateAntikinoRoom/{promocode_id}", response_class=JSONResponse)
async def update_promocode(request: Request, promocode_id: int, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    room_index = int(data.get("roomIndex"))
    new_address = data.get("address")
    new_price = data.get("price")

    print('Полученные данные: \n'
          f'Комната: {room_index}\n'
          f'Адрес: {new_address}\n'
          f'Цена: {new_price}')

    # Используем запрос для получения промокода по ID
    result = await session.execute(select(UserCode).where(UserCode.id == promocode_id))
    promocode = result.scalars().first()

    if promocode is None:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Если domain_config хранится как строка, нужно его десериализовать
    try:
        config1 = json.loads(promocode.domain_config)  # Преобразование JSON-строки в словарь
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Неверный формат domain_config")

    print(config1)

    # Проверяем, что это словарь и содержит ключ 'rooms'
    if not isinstance(config1, dict) or 'rooms' not in config1:
        raise HTTPException(status_code=400, detail="Неверная конфигурация промокода")

    rooms = config1['rooms']

    # Проверка индекса комнаты
    if room_index < 0 or room_index >= len(rooms):
        raise HTTPException(status_code=400, detail="Неверный индекс комнаты")

    # Обновляем адрес и цену
    rooms[room_index]['address'] = new_address
    rooms[room_index]['price'] = new_price

    # Сохранение обновленного domain_config в базе данных
    promocode.domain_config = json.dumps(config1)  # Сериализуем обратно в строку

    # Выполняем обновление записи в базе данных
    await session.execute(
        update(UserCode)
        .where(UserCode.id == promocode_id)
        .values(domain_config=promocode.domain_config)
    )
    await session.commit()

    return {"message": "Данные успешно обновлены"}
