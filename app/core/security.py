from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import KEYCLOAK_CLIENT_PUBLIC_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str = Depends(oauth2_scheme)):
    public_key = (
        "-----BEGIN PUBLIC KEY-----\n"
        + KEYCLOAK_CLIENT_PUBLIC_KEY
        + "\n-----END PUBLIC KEY-----"
    )

    try:
        return jwt.decode(
            token, public_key, algorithms=["RS256"], options={"verify_aud": False}
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
