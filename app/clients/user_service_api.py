import httpx
from fastapi import HTTPException, status, Request
from app.core.config import (
    USER_SERVICE_HOST,
)


async def get_children_for_parent(parent_id: str, request: Request) -> list[str]:
    """
    Calls the UserService to get a list of child IDs for the given parent.
    Propagates the Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # To nie powinno się zdarzyć, jeśli endpoint jest chroniony CurrentUserDep
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    headers = {"Authorization": auth_header}
    url = f"{USER_SERVICE_HOST}/api/v1/users/current/children"  # Dostosuj URL do twojego UserService

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()  # Rzuci wyjątek dla 4xx/5xx
            children_data = (
                response.json()
            )  # Oczekuje listy obiektów child z polem 'id'
            child_ids = [child.get("id") for child in children_data if child.get("id")]
            return child_ids
        except httpx.HTTPStatusError as e:
            # Przekaż błąd z UserService lub zwróć własny
            detail = (
                f"Error fetching children from User Service: {e.response.status_code}"
            )
            try:
                detail += f" - {e.response.json().get('detail', '')}"
            except Exception:
                pass
            raise HTTPException(
                status_code=e.response.status_code, detail=detail
            ) from e

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not connect to User Service: {e}",
            ) from e

        except Exception as e:  # Ogólny błąd
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while communicating with User Service: {str(e)}",
            ) from e
