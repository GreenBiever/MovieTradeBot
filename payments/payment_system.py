from enum import Enum
from typing import Type

from services import get_project_var_service

from .payment.currency import PaymentCurrencies, PaymentCurrency
from .payment.direct_payment import DirectPayment


class PaymentType(Enum):
    FIRST_PAYMENT = 'first'
    REFUND = 'refund'
    DIRECT_PAYMENT = 'direct'

    @classmethod
    def is_type_string_valid(cls, type_string: str):
        for member in cls:
            if member.value == type_string:
                return True

        return False


class PaymentSystemWorkMode(Enum):
    DEFAULT = 1
    CARD_MODE = 2


class PaymentSystem:

    async def init_payment(self, payment_type: PaymentType, **payment_data) -> PaymentT:
        payment_data['currency_id'] = 1  # Temporary

        payment_cls = self.__get_payment_cls_by_type(payment_type)
        new_payment = await payment_cls.create(**payment_data)
        return new_payment

    async def get_payment_by_uuid(self, payment_uuid: str) -> PaymentT | None:
        payment_pool = await get_payment_pool()
        return await payment_pool.get_payment(payment_uuid)

    @classmethod
    def is_direct_payment(cls, payment: PaymentT) -> bool:
        return type(payment) == DirectPayment

    @classmethod
    async def get_currency_by_id(cls, currency_id: int) -> PaymentCurrency:
        return PaymentCurrencies.from_id(currency_id)

    async def get_gateway_url(self) -> str:
        pass

    async def get_work_mode(self) -> PaymentSystemWorkMode:
        pass

    async def set_work_mode(self, work_mode: PaymentSystemWorkMode):
        """
        Set working mode for payments processing
        :return:
        """

    async def get_direct_payment_card_number(self) -> str:
        project_var = get_project_var_service()
        return await project_var.get('payment_system_direct_payment_cc_num')

    async def set_direct_payment_card_number(self, card_number: str):
        project_var = get_project_var_service()
        await project_var.set('payment_system_direct_payment_cc_num', card_number)

    async def get_direct_payment_card_holder(self) -> str:
        project_var = get_project_var_service()
        return await project_var.get('payment_system_direct_payment_cc_holder')

    async def set_direct_payment_card_holder(self, card_holder: str):
        project_var = get_project_var_service()
        await project_var.set('payment_system_direct_payment_cc_holder', card_holder)

    async def get_direct_payment_sbp_phone(self) -> str:
        project_var = get_project_var_service()
        return await project_var.get('payment_system_direct_payment_sbp_phone')

    async def set_direct_payment_sbp_phone(self, phone_number: str):
        project_var = get_project_var_service()
        await project_var.set('payment_system_direct_payment_sbp_phone', phone_number)

    async def get_direct_payment_lifetime(self) -> int:
        project_var = get_project_var_service()
        return int(await project_var.get('payment_system_direct_payment_lifetime'))

    async def set_direct_payment_lifetime(self, lifetime: int):
        project_var = get_project_var_service()
        await project_var.set('payment_system_direct_payment_lifetime', lifetime)

    async def get_bank_emit_for_card(self, card_number: str):
        pass

    async def _get_bank_emit_from_cache(self, card_number: str) -> str | None:
        pass

    async def _resolve_bank_emit(self, card_number: str):
        pass

    @classmethod
    def __get_payment_cls_by_type(cls, payment_type: PaymentType) -> Type[PaymentT]:
        return {
            PaymentType.FIRST_PAYMENT: Payment,
            PaymentType.REFUND: PaymentRefund,
            PaymentType.DIRECT_PAYMENT: DirectPayment
        }.get(payment_type)
