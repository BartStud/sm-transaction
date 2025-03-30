import uuid
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class AccountBase(BaseModel):
    pass


class AccountRead(AccountBase):
    id: uuid.UUID
    user_id: str
    balance: Decimal = Field(..., decimal_places=2)
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True  # Pydantic v2: from_attributes = True
