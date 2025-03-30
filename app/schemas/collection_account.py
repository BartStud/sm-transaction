import uuid
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

# Jeśli używasz statusu w modelu:
# from app.models.collection_account import CollectionAccountStatus


class CollectionAccountBase(BaseModel):  # Zmieniono nazwę
    collection_id: str  # Zmieniono nazwę pola
    balance: Decimal = Field(..., decimal_places=2)
    # Jeśli używasz statusu:
    # status: CollectionAccountStatus


class CollectionAccountRead(CollectionAccountBase):  # Zmieniono nazwę
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
        use_enum_values = True
