import uuid
import enum
from sqlalchemy import (
    Column,
    String,
    Numeric,
    DateTime,
    func,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class TransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"


class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Konto użytkownika powiązane z transakcją
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(
        SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING
    )
    amount = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String, nullable=True)

    # ID zbiórki, której dotyczy płatność/zwrot
    collection_id = Column(String, nullable=True, index=True)  # Zmieniona nazwa pola

    # ID ucznia, którego dotyczy płatność (jeśli dotyczy)
    student_id = Column(String, nullable=True, index=True)  # Zmieniona nazwa pola

    # ID transakcji zewnętrznej (np. bramka płatnicza)
    external_transaction_id = Column(String, nullable=True, unique=True, index=True)
