from uuid import UUID

from sqlalchemy import select

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for RefreshToken.

    Does NOT extend BaseRepository because RefreshToken intentionally
    does NOT inherit BaseModel (no audit columns).
    """

    def __init__(self, session) -> None:
        self._session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def get_by_token(self, raw_token: str) -> RefreshToken | None:
        """Look up a token by hashing the raw value the client provided."""
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.token == hash_token(raw_token)))
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: UUID) -> list[RefreshToken]:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
        )
        return list(result.scalars().all())

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        token.is_revoked = True
        await self._session.flush()
        return token

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        tokens = await self.get_all_for_user(user_id)
        for t in tokens:
            t.is_revoked = True
        await self._session.flush()

    async def delete(self, token: RefreshToken) -> None:
        await self._session.delete(token)
        await self._session.flush()
