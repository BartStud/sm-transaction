from typing import Annotated
from fastapi import Depends, HTTPException
from starlette import status

from app.core.security import verify_token


async def get_current_user(user=Depends(verify_token)):
    return user


CurrentUserDep = Annotated[dict, Depends(get_current_user)]


def get_current_user_id(payload: dict = Depends(verify_token)) -> str:
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials, user ID missing",
        )
    return user_id


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]
