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
from databases.models import User, UserGroup, UserRoles, UserCode, Hosting_Website, UserCodeType, Trade_User
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
    if promocode:
        return {'id': promocode.id, 'name': promocode.name, 'type': promocode.type_id, "user_id": promocode.user_id, "config": promocode.domain_config}
    else:
        raise HTTPException(status_code=404, detail="Промокод не найден")

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
                {"address": "Адрес комнаты 1", "price": 150, "services": []},
                {"address": "Адрес комнаты 2", "price": 200, "services": []},
                {"address": "Адрес комнаты 3", "price": 250, "services": []}
            ]
        }
    elif type_id == "2":
        settings = {
            "country": "EU",
            "language": "EN",
            "currency": "UAH",
            "prices": {
                "1-4": 100,
                "5-9": 150,
                "10-12": 200,
                "Ложа": 300
            },
            "seats": 50  # в процентах
        }
    elif type_id == "3":
        settings = {
            "country": "EU",
            "language": "EN",
            "currency": "UAH",
            "exhibitions": []
        }
    elif type_id == "4":
        settings = {
            "currency": "USD",
            "language": "EN"
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


@router.post("/promocodeUpdateAntikinoServices/{promocode_id}", response_class=JSONResponse)
async def update_promocode(request: Request, promocode_id: int, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    room_index = int(data.get("room"))
    service_name = data.get('name')
    service_price = data.get('price')

    result = await session.execute(select(UserCode).where(UserCode.id == promocode_id))
    promocode = result.scalars().first()

    if promocode is None:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Если domain_config хранится как строка, нужно его десериализовать
    try:
        config1 = json.loads(promocode.domain_config)  # Преобразование JSON-строки в словарь
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Неверный формат domain_config")

    rooms = config1['rooms']

    # Проверка индекса комнаты
    if room_index < 0 or room_index >= len(rooms):
        raise HTTPException(status_code=400, detail="Неверный индекс комнаты")

    # Извлекаем услуги комнаты
    services = rooms[room_index].get('services', [])

    # Проверка, существует ли услуга, и обновление или добавление
    service_found = False
    for service in services:
        if service['name'] == service_name:
            service['price'] = service_price  # Обновляем цену существующей услуги
            service_found = True
            break

    if not service_found:
        # Если услуга не найдена, добавляем новую
        services.append({"name": service_name, "price": service_price})

    # Обновляем список услуг в комнате
    rooms[room_index]['services'] = services
    promocode.domain_config = json.dumps(config1)

    await session.execute(
        update(UserCode)
        .where(UserCode.id == promocode_id)
        .values(domain_config=promocode.domain_config)
    )
    await session.commit()

    return {"message": "Данные успешно обновлены"}


@router.post("/promocodeDeleteAntikinoService/{promocode_id}", response_class=JSONResponse)
async def delete_service(request: Request, promocode_id: int, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    room_index = int(data.get("room"))
    service_name = data.get('name')

    result = await session.execute(select(UserCode).where(UserCode.id == promocode_id))
    promocode = result.scalars().first()

    if promocode is None:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Десериализуем domain_config
    try:
        config1 = json.loads(promocode.domain_config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Неверный формат domain_config")

    rooms = config1['rooms']

    # Проверка индекса комнаты
    if room_index < 0 or room_index >= len(rooms):
        raise HTTPException(status_code=400, detail="Неверный индекс комнаты")

    # Извлекаем услуги комнаты
    services = rooms[room_index].get('services', [])

    # Удаляем услугу, если она существует
    services = [service for service in services if service['name'] != service_name]

    # Обновляем список услуг в комнате
    rooms[room_index]['services'] = services
    promocode.domain_config = json.dumps(config1)

    await session.execute(
        update(UserCode)
        .where(UserCode.id == promocode_id)
        .values(domain_config=promocode.domain_config)
    )
    await session.commit()

    return {"message": "Услуга успешно удалена"}


@router.post('/updatePricesTheatre/{promocode_id}', response_class=JSONResponse)
async def update_teatre_prices(request: Request, promocode_id: int,
                               session: AsyncSession = Depends(get_session)):
    data = await request.json()
    prices = data.get('prices')

    # Получаем промокод из БД
    promocode = await get_promocode_by_id(session, promocode_id)
    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Попробуем десериализовать domain_config
    try:
        domain_config = json.loads(promocode.domain_config)  # Десериализация
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка декодирования конфигурации")

    # Обновляем настройки цен
    domain_config['prices'] = prices  # Обновляем в структуре
    promocode.domain_config = json.dumps(domain_config)  # Сериализация обратно в строку

    # Сохраняем изменения в БД
    session.add(promocode)
    await session.commit()

    return {"message": "Настройки цен успешно обновлены"}


@router.post('/updateSeatsTheatre/{promocode_id}', response_class=JSONResponse)
async def update_teatre_prices(request: Request, promocode_id: int,
                               session: AsyncSession = Depends(get_session)):
    data = await request.json()
    seats = data.get('seats')

    # Получаем промокод из БД
    promocode = await get_promocode_by_id(session, promocode_id)
    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Попробуем десериализовать domain_config
    try:
        domain_config = json.loads(promocode.domain_config)  # Десериализация
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка декодирования конфигурации")

    # Обновляем настройки цен
    domain_config['seats'] = seats  # Обновляем в структуре
    promocode.domain_config = json.dumps(domain_config)  # Сериализация обратно в строку

    # Сохраняем изменения в БД
    session.add(promocode)
    await session.commit()

    return {"message": "Настройки свободных сидений успешно обновлены"}


@router.post('/updateExhibtions/{promocode_id}', response_class=JSONResponse)
async def update_exhibitions(request: Request, promocode_id: int, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    exhibitions = data.get('exhibitions')

    # Получаем промокод из БД
    promocode = await get_promocode_by_id(session, promocode_id)
    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Попробуем десериализовать domain_config
    try:
        domain_config = json.loads(promocode.domain_config)  # Десериализация
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка декодирования конфигурации")

    domain_config['exhibitions'] = exhibitions
    promocode.domain_config = json.dumps(domain_config)

    session.add(promocode)
    await session.commit()

    return {"message": "Настройки выставок успешно обновлены"}


@router.post('/removeExhibition/{promocode_id}', response_class=JSONResponse)
async def remove_exhibition(request: Request, promocode_id: int, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    index = data.get('index')

    # Получаем промокод из БД
    promocode = await get_promocode_by_id(session, promocode_id)
    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Попробуем десериализовать domain_config
    try:
        domain_config = json.loads(promocode.domain_config)  # Десериализация
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка декодирования конфигурации")

    # Удаляем выставку по индексу
    if index is None or index < 0 or index >= len(domain_config.get('exhibitions', [])):
        raise HTTPException(status_code=400, detail="Некорректный индекс")

    domain_config['exhibitions'].pop(index)
    promocode.domain_config = json.dumps(domain_config)

    session.add(promocode)
    await session.commit()

    return {"message": "Выставка успешно удалена"}


@router.post("/promocodeUpdateTrade/{code_id}", response_class=JSONResponse)
async def update_trade_promocode(request: Request, code_id: int = Path(...),
                                 session: AsyncSession = Depends(get_session)):
    data = await request.json()
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
        "language": language,
        "currency": currency
    })
    user_code.domain_config = json.dumps(settings)

    # Сохраняем изменения в базе данных
    session.add(user_code)
    await session.commit()

    return {"message": "Promocode updated successfully"}


# Роутеры для контроля рефералов в трейд сайте
@router.get("/promo_get_trade_users/{referer_id}", response_class=JSONResponse)
async def get_trade_users(referer_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Trade_User).where(Trade_User.referer_id == referer_id))
    users = result.scalars().all()
    users_dict = {}
    if users:
        for user in users:
            users_dict[user.id] = {
                "username": user.username,
                "balance": user.balance
            }

        return JSONResponse(content={"users": users_dict})
    else:
        raise HTTPException(status_code=404, detail="Пользователи не найдены")


@router.get("/promo_trade_get_user/{user_id}", response_class=JSONResponse)
async def get_trade_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Trade_User).where(Trade_User.id == user_id))
    user = result.scalars().first()
    if user:
        text = {"username": user.username, "balance": user.balance, "currency": user.currency.name.upper(), "referer_id": user.referer_id, "status":  user.status, "is_verified": user.is_verified, "min_withdraw": user.min_withdraw, "is_withdraw": user.is_withdraw, "luck": user.luck}
        return JSONResponse(content=text)
    else:
        raise HTTPException(status_code=404, detail="Пользователь не найден")