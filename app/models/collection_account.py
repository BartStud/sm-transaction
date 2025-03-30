import uuid
import enum
from sqlalchemy import Column, String, Numeric, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


# Możesz używać tego statusu lub polegać wyłącznie na statusie z serwisu Collections
class CollectionAccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class CollectionAccount(Base):
    __tablename__ = "collection_accounts"  # Zmieniona nazwa tabeli

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ID zbiórki (collection) z zewnętrznego serwisu
    collection_id = Column(
        String, unique=True, index=True, nullable=False
    )  # Zmieniona nazwa pola
    balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    # Status może być replikowany lub zarządzany tylko w Collection Service
    # Dla uproszczenia i mniejszego couplingu, można usunąć to pole
    # status = Column(SQLEnum(CollectionAccountStatus), nullable=False, default=CollectionAccountStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
