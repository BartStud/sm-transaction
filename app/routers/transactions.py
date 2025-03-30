from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List

from app.schemas.transaction import (
    TransactionRead,
    TransactionPaymentRequest,
    TransactionDepositRequest,
    TransactionWithdrawalRequest,
    RefundRequest,  # Internal refund request schema
    StudentPaymentSummary,
    StudentPaymentSummaryBatchRequest,
    StudentPaymentSummaryBatchResponse,
)
from app.services.transaction_service import transaction_service
from app.dependencies.db import DatabaseDep
from app.dependencies.auth import UserIdDep  # User ID from token

# TODO: Add dependencies for service-to-service or admin authorization
# from app.dependencies.auth import verify_service_token, require_admin_role

router = APIRouter()


@router.post(
    "/deposit",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a deposit into user account",
)
async def initiate_deposit_endpoint(
    db: DatabaseDep,
    current_user_id: UserIdDep,
    deposit_request: TransactionDepositRequest,
):
    """
    Initiates the process of depositing funds into the user's internal account.
    (Simplified simulation - marks as completed immediately).
    """
    # Use commit/rollback block for top-level operations
    try:
        transaction = await transaction_service.initiate_deposit(
            db=db, user_id=current_user_id, deposit_data=deposit_request
        )
        await db.commit()
        return transaction
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        print(f"Error during deposit initiation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deposit initiation failed.",
        )


@router.post(
    "/withdraw",
    response_model=TransactionRead,
    status_code=status.HTTP_202_ACCEPTED,  # 202 Accepted for async/pending operations
    summary="Request a withdrawal from user account",
)
async def request_withdrawal_endpoint(
    db: DatabaseDep,
    current_user_id: UserIdDep,
    withdrawal_request: TransactionWithdrawalRequest,
):
    """
    Requests a withdrawal of funds from the user's internal account.
    Creates a PENDING transaction. Requires sufficient funds.
    """
    try:
        transaction = await transaction_service.initiate_withdrawal(
            db=db, user_id=current_user_id, withdrawal_data=withdrawal_request
        )
        await db.commit()
        return transaction
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        print(f"Error during withdrawal request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Withdrawal request failed.",
        )


@router.post(
    "/pay",  # Endpoint for paying towards a collection
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Pay for a collection",  # Zmieniono summary
)
async def pay_for_collection_endpoint(  # Zmieniono nazwę funkcji
    db: DatabaseDep,
    current_user_id: UserIdDep,
    payment_request: TransactionPaymentRequest,  # Używa zaktualizowanego schematu
):
    """
    Pays a specific amount from the user's internal account for a given collection
    and student. Requires sufficient funds.
    """
    try:
        # make_payment handles the nested transaction internally
        transaction = await transaction_service.make_payment(
            db=db, user_id=current_user_id, payment_data=payment_request
        )
        await db.commit()  # Commit the outer transaction
        return transaction
    except HTTPException as e:
        await db.rollback()  # Rollback outer transaction on error
        raise e
    except Exception as e:
        await db.rollback()
        print(f"Error during payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during payment processing.",
        )


@router.get(
    "/me",
    response_model=List[TransactionRead],
    summary="Get current user's transaction history",
)
async def read_transactions_me(
    db: DatabaseDep,
    current_user_id: UserIdDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieves a list of the current user's past transactions, ordered by date descending.
    Supports pagination using `skip` and `limit` query parameters.
    """
    transactions = await transaction_service.get_user_transactions(
        db=db, user_id=current_user_id, skip=skip, limit=limit
    )
    return transactions


# === Internal / Service-to-Service / Admin Endpoints ===


@router.post(
    "/internal/refund",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Process a refund (Internal/Admin/Service)",
    # dependencies=[Depends(require_admin_or_service_role)] # TODO: Secure this endpoint!
)
async def process_refund_endpoint(
    db: DatabaseDep,
    refund_request: RefundRequest = Body(...),  # Używa zaktualizowanego schematu
):
    """
    Processes a refund to a user's account from a collection account.
    **Security:** This endpoint MUST be protected and only accessible by
    authorized services or administrators.
    """
    # TODO: Add permission check logic here
    print(f"Received internal refund request: {refund_request}")
    try:
        # process_refund handles the nested transaction internally
        transaction = await transaction_service.process_refund(
            db=db,
            user_id=refund_request.user_id,
            collection_id=refund_request.collection_id,  # Zmieniono pole
            amount=refund_request.amount,
            description=refund_request.description,
        )
        await db.commit()  # Commit outer transaction
        return transaction
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        print(f"Error during refund processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during refund processing.",
        )


@router.post(
    "/summary/student-collection-payments",  # Zmieniono ścieżkę
    response_model=StudentPaymentSummaryBatchResponse,
    summary="Get total paid amount for student-collection pairs (Service)",  # Zmieniono summary
    # dependencies=[Depends(verify_service_token)] # TODO: Secure this endpoint!
)
async def get_student_collection_payment_summaries(  # Zmieniono nazwę funkcji
    db: DatabaseDep,
    batch_request: StudentPaymentSummaryBatchRequest,  # Używa zaktualizowanego schematu
):
    """
    Retrieves the total completed payment amount for a list of specific students
    towards specific collections.

    Intended for service-to-service communication (e.g., called by the Collection Service)
    and MUST be secured appropriately.
    """
    if not batch_request.requests:
        return StudentPaymentSummaryBatchResponse(summaries=[])

    # No db transaction needed for read operation
    summaries = await transaction_service.get_students_paid_summaries(
        db, batch_request.requests
    )
    return StudentPaymentSummaryBatchResponse(summaries=summaries)
