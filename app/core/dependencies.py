from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=True)

# Re-export a typed dependency alias for DB sessions
DBSession = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_user(
    request: Request,
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    """Extract and validate the JWT bearer token, then return the User ORM object.

    Importing here (not at top-level) to avoid circular imports between
    models ↔ dependencies.
    """
    from app.repositories.user import UserRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    # Write the validated user_id into request.state so the logging middleware
    # can read it AFTER call_next completes (correct timing, avoids early-decode bug).
    request.state.user_id = str(user.id)
    return user


# Typed alias for routes that require authentication
CurrentUser = Annotated[object, Depends(get_current_user)]


def get_client_source(request: Request) -> str:
    """Return the server-normalised request origin (web / android / ios / api)."""
    return getattr(request.state, "source", "api")


ClientSource = Annotated[str, Depends(get_client_source)]
