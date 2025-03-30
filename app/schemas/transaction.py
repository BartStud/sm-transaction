import uuid
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime
from typing import List
from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransactionCreateInternal(TransactionBase):  # Renamed for clarity
    # Internal schema used by services
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING  # Default status internal
    description: str | None = None
    collection_id: str | None = None  # Zmieniono nazwę
    student_id: str | None = None  # Zmieniono nazwę
    account_id: uuid.UUID  # Required when creating
    external_transaction_id: str | None = None


class TransactionDepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransactionWithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    # external_account_details: str # Example


class TransactionPaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    collection_id: str = Field(
        ..., description="ID of the collection (from Collection Service)"
    )  # Zmieniono nazwę
    student_id: str = Field(
        ..., description="ID of the student the payment is for"
    )  # Zmieniono nazwę
    description: str | None = None


class RefundRequest(BaseModel):  # Schema for internal refund endpoint
    user_id: str
    collection_id: str  # Zmieniono nazwę
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str | None = None


class TransactionRead(TransactionBase):
    id: uuid.UUID
    account_id: uuid.UUID
    type: TransactionType
    status: TransactionStatus
    timestamp: datetime
    description: str | None = None
    collection_id: str | None = None  # Zmieniono nazwę
    student_id: str | None = None  # Zmieniono nazwę
    external_transaction_id: str | None = None

    class Config:
        orm_mode = True
        use_enum_values = True


# Schemas for student payment summary endpoint
class StudentPaymentSummary(BaseModel):
    collection_id: str  # Zmieniono nazwę
    student_id: str
    total_paid: Decimal = Field(..., decimal_places=2)


class StudentPaymentSummaryRequestItem(BaseModel):
    collection_id: str  # Zmieniono nazwę
    student_id: str


class StudentPaymentSummaryBatchRequest(BaseModel):
    requests: List[StudentPaymentSummaryRequestItem]


class StudentPaymentSummaryBatchResponse(BaseModel):
    summaries: List[StudentPaymentSummary]
