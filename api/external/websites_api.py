from datetime import datetime
from typing import Optional

from aiogram import Bot
import json
import config
from databases.connect import get_session
from databases.crud import get_user_by_tg_id, get_promocodes_by_user, get_promocode_by_id, get_websites, \
    get_promocode_types, get_hosting_website, get_promocode_by_name
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Query, Request, Path, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

bot: Bot = Bot(config.BOT_TOKEN)
router = APIRouter()


@router.get("/{promocodeName}", response_class=JSONResponse)
async def get_promocode(request: Request, promocodeName: int = Path(...), session: AsyncSession = Depends(get_session)):
    promocode = await get_promocode_by_name(session, promocodeName)
    id = promocode.id
    name = promocode.name
    type = promocode.type_id
    domain_config = promocode.domain_config
    return {'id': id, 'name': name, 'type': type, "config": domain_config}
