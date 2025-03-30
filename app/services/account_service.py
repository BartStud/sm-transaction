import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.account import Account
from app.schemas.account import AccountRead


class AccountService:

    async def get_account_by_user_id(
        self, db: AsyncSession, user_id: str
    ) -> Account | None:
        result = await db.execute(select(Account).filter(Account.user_id == user_id))
        return result.scalars().first()

    async def get_or_create_account(self, db: AsyncSession, user_id: str) -> Account:
        account = await self.get_account_by_user_id(db, user_id)
        if not account:
            print(f"Creating new account for user_id: {user_id}")
            account = Account(user_id=user_id, balance=Decimal("0.00"))
            db.add(account)
            # Commit and refresh managed by caller or transaction context
            await db.flush([account])  # Assign ID if needed before commit
            print(f"Account object created for {user_id}, pending commit.")
        return account

    async def get_account_details(self, db: AsyncSession, user_id: str) -> AccountRead:
        account = await self.get_or_create_account(db, user_id)
        return AccountRead.from_orm(account)

    async def _update_balance_unsafe(
        self, db: AsyncSession, account_id: uuid.UUID, change: Decimal
    ) -> Account:
        # Retrieve account with lock
        result = await db.execute(
            select(Account).filter(Account.id == account_id).with_for_update()
        )
        account = result.scalars().first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found during balance update",
            )

        new_balance = account.balance + change
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds"
            )

        account.balance = new_balance
        db.add(account)  # Add to session to mark modified
        return account


account_service = AccountService()
