import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.collection_account import CollectionAccount  # , CollectionAccountStatus
from app.schemas.collection_account import CollectionAccountRead


class CollectionAccountService:  # Zmieniono nazwę klasy

    async def get_collection_account_by_collection_id(  # Zmieniono nazwę metody i parametr
        self, db: AsyncSession, collection_id: str
    ) -> CollectionAccount | None:
        result = await db.execute(
            select(CollectionAccount).filter(
                CollectionAccount.collection_id == collection_id
            )  # Zmieniono model i pole
        )
        return result.scalars().first()

    async def get_or_create_collection_account(  # Zmieniono nazwę metody i parametr
        self, db: AsyncSession, collection_id: str
    ) -> CollectionAccount:
        # Consider validating collection_id against the Collection Service first if needed
        account = await self.get_collection_account_by_collection_id(
            db, collection_id
        )  # Zmieniono wywołanie
        if not account:
            print(f"Creating new collection account for collection_id: {collection_id}")
            account = CollectionAccount(  # Zmieniono model
                collection_id=collection_id,  # Zmieniono pole
                balance=Decimal("0.00"),
                # status=CollectionAccountStatus.ACTIVE # Jeśli używasz statusu
            )
            db.add(account)
            await db.flush([account])  # Assign ID if needed before commit
            print(
                f"Collection account object created for {collection_id}, pending commit."
            )
        # Jeśli używasz statusu:
        # elif account.status != CollectionAccountStatus.ACTIVE:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Collection {collection_id} is not active ({account.status}). Cannot process transaction."
        #     )
        return account

    async def get_collection_account_details(  # Zmieniono nazwę metody i parametr
        self, db: AsyncSession, collection_id: str
    ) -> CollectionAccountRead | None:
        account = await self.get_collection_account_by_collection_id(
            db, collection_id
        )  # Zmieniono wywołanie
        if account:
            return CollectionAccountRead.from_orm(account)  # Zmieniono schemat
        return None

    async def _update_collection_balance_unsafe(  # Zmieniono nazwę metody i parametr
        self, db: AsyncSession, collection_account_id: uuid.UUID, change: Decimal
    ) -> CollectionAccount:
        result = await db.execute(
            select(CollectionAccount)
            .filter(CollectionAccount.id == collection_account_id)
            .with_for_update()  # Zmieniono model
        )
        account = result.scalars().first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection account not found during balance update",  # Zmieniono komunikat
            )

        # Jeśli używasz statusu:
        # if account.status != CollectionAccountStatus.ACTIVE:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Cannot update balance for non-active collection ({account.collection_id}, status: {account.status})"
        #     )

        new_balance = account.balance + change
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds in collection account {account.collection_id} for this operation.",  # Zmieniono komunikat
            )

        account.balance = new_balance
        db.add(account)
        return account


collection_account_service = CollectionAccountService()  # Zmieniono nazwę instancji
