from fastapi import APIRouter, Depends

from app.schemas.account import AccountRead
from app.services.account_service import account_service
from app.dependencies.db import DatabaseDep
from app.dependencies.auth import CurrentUserIdDep

router = APIRouter()


@router.get(
    "/me", response_model=AccountRead, summary="Get current user's account details"
)
async def read_account_me(
    db: DatabaseDep,
    current_user_id: CurrentUserIdDep,
):
    """
    Retrieves the details of the currently logged-in user's internal account,
    including the current balance. Creates the account if it doesn't exist.
    """
    # get_account_details includes get_or_create logic
    account = await account_service.get_account_details(db=db, user_id=current_user_id)
    return account
