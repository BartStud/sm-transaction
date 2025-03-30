from fastapi import APIRouter

from app.routers import accounts, collection_accounts, transactions

api_router = APIRouter()
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(
    collection_accounts.router,
    prefix="/collection_accounts",
    tags=["Collection Accounts"],
)
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["Transactions"]
)
