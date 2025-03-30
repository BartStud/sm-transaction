from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL


async def get_db():
    engine = create_async_engine(DATABASE_URL, echo=True)
    session_local = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_local() as session:
        yield session


DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
