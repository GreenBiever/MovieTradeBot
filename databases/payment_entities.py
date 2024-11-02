# databases/payment_entities.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .connect import Base  # Предполагается, что Base уже импортирован в проекте.


class PaymentProcessStrategy:
    DEFAULT = 1
    REINIT_AS_FAST_PAYMENT = 2


class PaymentBank(Base):
    __tablename__ = 'payment_bank'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True)
    payment_process_strategy_id = Column(Integer, default=PaymentProcessStrategy.DEFAULT)
