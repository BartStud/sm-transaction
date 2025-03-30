import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, and_, or_
from decimal import Decimal
from fastapi import HTTPException, status
from typing import List

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.account import Account
from app.models.collection_account import CollectionAccount  # Zmieniono import
from app.schemas.transaction import (
    TransactionCreateInternal,  # Use internal schema
    TransactionRead,
    TransactionPaymentRequest,
    TransactionDepositRequest,
    TransactionWithdrawalRequest,
    StudentPaymentSummaryRequestItem,
    StudentPaymentSummary,
)
from app.services.account_service import account_service
from app.services.collection_account_service import (
    collection_account_service,
)  # Zmieniono import


class TransactionService:

    async def _create_transaction_record_internal(  # Renamed for clarity
        self, db: AsyncSession, transaction_data: TransactionCreateInternal
    ) -> Transaction:
        """Internal helper to create and add a transaction record."""
        db_transaction = Transaction(**transaction_data.dict())
        db.add(db_transaction)
        await db.flush([db_transaction])  # Assign ID
        return db_transaction

    async def make_payment(
        self, db: AsyncSession, user_id: str, payment_data: TransactionPaymentRequest
    ) -> TransactionRead:
        """Processes payment: Debits user, credits collection account."""
        async with db.begin_nested():  # Use savepoint for atomicity
            # 1. Get/Create user account
            user_account = await account_service.get_or_create_account(db, user_id)

            # 2. Get/Create collection account
            # This will raise HTTPException if collection is inactive (if status is used)
            collection_account = (
                await collection_account_service.get_or_create_collection_account(
                    db, payment_data.collection_id  # Zmieniono pole
                )
            )
            # Ensure IDs are available after potential creation
            await db.flush()

            # 3. Lock both accounts (consistent order: user then collection)
            locked_user_account = await account_service._update_balance_unsafe(
                db,
                account_id=user_account.id,
                change=-payment_data.amount,  # Debits and locks user acc
            )
            # _update_balance_unsafe already performed the balance check and update

            locked_collection_account = (
                await collection_account_service._update_collection_balance_unsafe(
                    db,
                    collection_account_id=collection_account.id,
                    change=payment_data.amount,  # Credits and locks collection acc
                )
            )
            # _update_collection_balance_unsafe already performed the update

            # 4. Create transaction record (linked to user account)
            transaction_create = TransactionCreateInternal(
                account_id=locked_user_account.id,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED,  # Payments are completed immediately internally
                amount=payment_data.amount,
                description=payment_data.description
                or f"Payment for collection {payment_data.collection_id}",  # Zmieniono komunikat
                collection_id=payment_data.collection_id,  # Zmieniono pole
                student_id=payment_data.student_id,  # Zmieniono pole
            )
            db_transaction = await self._create_transaction_record_internal(
                db, transaction_data=transaction_create
            )

            # Nested transaction commits here automatically if no exceptions

        # Refresh objects after successful nested commit if needed for response
        await db.refresh(locked_user_account)
        await db.refresh(locked_collection_account)
        await db.refresh(db_transaction)

        print(
            f"Payment successful: User {user_id} paid {payment_data.amount} to collection {payment_data.collection_id}"
        )  # Zmieniono komunikat
        return TransactionRead.from_orm(db_transaction)

    async def process_refund(
        self,
        db: AsyncSession,
        user_id: str,
        collection_id: str,
        amount: Decimal,
        description: str | None = None,  # Zmieniono parametr
    ) -> TransactionRead:
        """Processes refund: Debits collection account, credits user account."""
        async with db.begin_nested():
            # 1. Get user account (must exist for refund)
            user_account = await account_service.get_account_by_user_id(db, user_id)
            if not user_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User account for user_id {user_id} not found for refund.",
                )

            # 2. Get collection account (must exist)
            collection_account = await collection_account_service.get_collection_account_by_collection_id(
                db, collection_id
            )  # Zmieniono wywołanie
            if not collection_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection account {collection_id} not found for refund.",
                )  # Zmieniono komunikat

            await db.flush()  # Ensure IDs

            # 3. Lock and update balances (consistent order)
            locked_collection_account = (
                await collection_account_service._update_collection_balance_unsafe(
                    db,
                    collection_account_id=collection_account.id,
                    change=-amount,  # Debits collection
                )
            )
            # Check for insufficient funds in collection account is done inside ^

            locked_user_account = await account_service._update_balance_unsafe(
                db, account_id=user_account.id, change=amount  # Credits user
            )

            # 4. Create refund transaction record
            transaction_create = TransactionCreateInternal(
                account_id=locked_user_account.id,
                type=TransactionType.REFUND,
                status=TransactionStatus.COMPLETED,  # Refunds are completed immediately internally
                amount=amount,
                description=description
                or f"Refund from collection {collection_id}",  # Zmieniono komunikat
                collection_id=collection_id,  # Zmieniono pole
                # student_id might not be relevant for all refunds
            )
            db_transaction = await self._create_transaction_record_internal(
                db, transaction_data=transaction_create
            )

        await db.refresh(locked_user_account)
        await db.refresh(locked_collection_account)
        await db.refresh(db_transaction)

        print(
            f"Refund successful: User {user_id} received {amount} from collection {collection_id}"
        )  # Zmieniono komunikat
        return TransactionRead.from_orm(db_transaction)

    async def initiate_deposit(
        self, db: AsyncSession, user_id: str, deposit_data: TransactionDepositRequest
    ) -> TransactionRead:
        """Initiates deposit process (simplified simulation)."""
        # Real scenario: Call payment gateway, get URL/ID, create PENDING transaction
        print(f"Initiating deposit for user {user_id}, amount {deposit_data.amount}")
        async with db.begin_nested():
            account = await account_service.get_or_create_account(db, user_id)
            await db.flush()

            # Simulate immediate completion for simplicity
            updated_account = await account_service._update_balance_unsafe(
                db, account_id=account.id, change=deposit_data.amount
            )

            transaction_create = TransactionCreateInternal(
                account_id=updated_account.id,
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED,  # Simulating immediate success
                amount=deposit_data.amount,
                description="Simulated deposit completed",
                external_transaction_id=f"sim_dep_{uuid.uuid4()}",
            )
            db_transaction = await self._create_transaction_record_internal(
                db, transaction_data=transaction_create
            )

        await db.refresh(updated_account)
        await db.refresh(db_transaction)
        print(
            f"Simulated deposit completed for user {user_id}, amount {deposit_data.amount}"
        )
        return TransactionRead.from_orm(db_transaction)

    async def initiate_withdrawal(
        self,
        db: AsyncSession,
        user_id: str,
        withdrawal_data: TransactionWithdrawalRequest,
    ) -> TransactionRead:
        """Initiates withdrawal process (creates PENDING transaction)."""
        # Real scenario: Validate details, call external payout API, update status via webhook/polling
        print(
            f"Initiating withdrawal for user {user_id}, amount {withdrawal_data.amount}"
        )
        async with db.begin_nested():
            account = await account_service.get_or_create_account(db, user_id)
            await db.flush()

            # Lock funds by debiting
            updated_account = await account_service._update_balance_unsafe(
                db, account_id=account.id, change=-withdrawal_data.amount
            )

            transaction_create = TransactionCreateInternal(
                account_id=updated_account.id,
                type=TransactionType.WITHDRAWAL,
                status=TransactionStatus.PENDING,  # Status is pending until external confirmation
                amount=withdrawal_data.amount,
                description=f"Withdrawal request",
                external_transaction_id=f"sim_wd_{uuid.uuid4()}",  # Example internal ID
            )
            db_transaction = await self._create_transaction_record_internal(
                db, transaction_data=transaction_create
            )

        await db.refresh(updated_account)
        await db.refresh(db_transaction)
        print(
            f"Withdrawal request created for user {user_id}, amount {withdrawal_data.amount}. Status: PENDING"
        )
        return TransactionRead.from_orm(db_transaction)

    async def get_user_transactions(
        self, db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[TransactionRead]:
        """Gets user's transaction history."""
        account = await account_service.get_account_by_user_id(db, user_id)
        if not account:
            return []

        result = await db.execute(
            select(Transaction)
            .filter(Transaction.account_id == account.id)
            .order_by(desc(Transaction.timestamp))
            .offset(skip)
            .limit(limit)
        )
        transactions = result.scalars().all()
        return [TransactionRead.from_orm(t) for t in transactions]

    async def get_students_paid_summaries(  # Renamed method for clarity
        self, db: AsyncSession, requests: List[StudentPaymentSummaryRequestItem]
    ) -> List[StudentPaymentSummary]:
        """Calculates the sum of completed payments for lists of (collection_id, student_id)."""
        if not requests:
            return []

        conditions = []
        for req in requests:
            conditions.append(
                and_(
                    Transaction.collection_id == req.collection_id,  # Zmieniono pole
                    Transaction.student_id == req.student_id,
                )
            )

        query = (
            select(
                Transaction.collection_id,  # Zmieniono pole
                Transaction.student_id,
                func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label(
                    "total_paid"
                ),
            )
            .where(
                Transaction.type == TransactionType.PAYMENT,
                Transaction.status == TransactionStatus.COMPLETED,
                or_(*conditions),
            )
            .group_by(
                Transaction.collection_id, Transaction.student_id
            )  # Zmieniono pole
        )

        result = await db.execute(query)
        paid_summaries_raw = result.all()

        paid_map = {
            (
                summary.collection_id,
                summary.student_id,
            ): summary.total_paid  # Zmieniono pole
            for summary in paid_summaries_raw
        }

        response_summaries = []
        for req in requests:
            total_paid = paid_map.get(
                (req.collection_id, req.student_id), Decimal("0.00")
            )  # Zmieniono pole
            response_summaries.append(
                StudentPaymentSummary(
                    collection_id=req.collection_id,  # Zmieniono pole
                    student_id=req.student_id,
                    total_paid=total_paid,
                )
            )

        return response_summaries


transaction_service = TransactionService()
