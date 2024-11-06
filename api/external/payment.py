from datetime import datetime
from typing import Optional

from aiogram import Bot
import json
import config
from databases.connect import get_session
from pydantic import BaseModel
from databases.crud import get_user_by_tg_id, get_promocodes_by_user, get_promocode_by_id, get_websites, \
    get_promocode_types, get_hosting_website, get_promocode_by_name
from api import UserResolver, UserResolveHandler
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from fastapi import APIRouter, Response, status as http_status, Depends

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

bot: Bot = Bot(config.BOT_TOKEN)
router = APIRouter(prefix='/payment')


class PaymentBase(BaseModel):
    """
    Base properties of any payment instance
    """
    amount: int
    initials: str
    website_id: int
    worker_resolve: UserResolver | dict
    currency_id: int = 1


class BasePaymentCreateRequest(PaymentBase):
    """
    Defines last payment id to check was payment paid
    """
    last_payment_id: str | None = None


class DefaultPaymentCreateRequest(BasePaymentCreateRequest):
    card_number: str
    card_expiry_year: str
    card_expiry_month: str
    card_cvv: str
    note: str = None
    ip_data: dict


class PaymentRefundCreateRequest(DefaultPaymentCreateRequest):
    pass


@router.post("/redirectToPayment", response_class=JSONResponse)
async def redirect_to_payment(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()
    promocode_name = data.get("promocodeName")
    website_id = data.get("websiteID")
    user_id = data.get("userID")
    language = data.get("language")
    currency = data.get("currency")
    initials = data.get("initials")
    phone = data.get("phone")
    amount = data.get("amount")


@router.post('/{payment_type}')
async def init_payment(
        payment_type: str,
        payment_data: DefaultPaymentCreateRequest | PaymentRefundCreateRequest,
        response: Response,
        payment_system: 'PaymentSystem' = Depends(get_payment_system),
        notifications=Depends(get_notify_service)
):
    worker = await UserResolveHandler(payment_data.worker_resolve).resolve()
    if worker is None:
        response.status_code = http_status.HTTP_400_BAD_REQUEST
        return PaymentApiErrorResponse(
            error_description='Entity not found'
        )

    notify_data = {
        'bank_emit': await resolve_bank_name_for_card(payment_data.card_number.replace(' ', '')),
        'note': payment_data.note,
        'ip': payment_data.ip_data['ip'],
        'location': payment_data.ip_data['location'],
        'initials': payment_data.initials
    }
    notify = Notifications.Mammoth.OnCardInput(
        chats_extend=worker.id,
        **notify_data
    )
    await notifications.notify(notify=notify)

    last_payment_id = payment_data.last_payment_id
    if last_payment_id is not None and (
    payment := await payment_system.get_payment_by_uuid(last_payment_id)) is not None:
        await _resend_existing_payment_log(payment)
        await payment.set_status(PaymentStatuses.WAITING_CARD_PROCESSED)
        return DefaultPaymentCreatedResponse(id=last_payment_id)

    if (payment_type := get_payment_type_from_str(payment_type)) is None:
        response.status_code = http_status.HTTP_400_BAD_REQUEST
        return PaymentApiErrorResponse(
            error_description='Entity not found'
        )

    prepared_data = dict(
        amount=payment_data.amount,
        worker_id=worker.id,
        website_id=payment_data.website_id,
        currency_id=payment_data.currency_id,
        initials=payment_data.initials,
        card_number=payment_data.card_number.replace(' ', ''),
        card_expiry_year=payment_data.card_expiry_year,
        card_expiry_month=payment_data.card_expiry_month,
        card_secure_code=payment_data.card_cvv,
        note=payment_data.note
    )

    new_payment = await payment_system.init_payment(payment_type, **prepared_data)
    chat_logs = get_chat_service().get('logs')
    await chat_logs.events.on_new_payment(new_payment)

    return paymentCreatedResponseClsByType.get(payment_type)(id=new_payment.uuid)
