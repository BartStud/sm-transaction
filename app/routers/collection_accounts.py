from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.collection_account import CollectionAccountRead
from app.services.collection_account_service import collection_account_service
from app.dependencies.db import DatabaseDep

# TODO: Add appropriate authorization dependency (e.g., check for admin or service role)
# from app.dependencies.auth import require_admin_or_service_role

router = APIRouter()


# Example endpoint - requires proper authorization!
@router.get(
    "/{collection_id}",  # Zmieniono parametr ścieżki
    response_model=CollectionAccountRead,
    summary="Get collection account details",
    # dependencies=[Depends(require_admin_or_service_role)] # Example protection
)
async def read_collection_account(  # Zmieniono nazwę funkcji i parametr
    collection_id: str,
    db: DatabaseDep,
):
    """
    Retrieves the details of a specific collection's internal account,
    including its current balance.
    Requires appropriate permissions.
    """
    account = await collection_account_service.get_collection_account_details(
        db, collection_id
    )  # Zmieniono wywołanie
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection account not found"
        )  # Zmieniono komunikat
    return account


# Potential endpoint for listing accounts (also needs protection)
# @router.get("", response_model=List[CollectionAccountRead], ...)
# async def list_collection_accounts(...): ...
