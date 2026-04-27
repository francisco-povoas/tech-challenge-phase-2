from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID

from jose import JWTError, jwt


class InvalidToken(Exception):
    pass


class JWTProvider:
    def __init__(self, secret_key: str, expire_minutes: int, algorithm: str) -> None:
        self._jwt = jwt
        self.secret_key = secret_key
        self.expire_minutes = expire_minutes
        self.algorithm = algorithm

    def decode(self, token: str) -> Dict[str, Any]:
        try:
            claims: Dict[str, Any] = self._jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return claims
        except JWTError as exc:
            raise InvalidToken from exc

    def create_access_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        to_encode = {**data.copy(), "exp": expire}
        access_token = self._jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return {
            "expire": expire.timestamp(),
            "access_token": access_token,
            "token_type": "bearer",
        }

    def get_sub(self, token: str) -> str:
        payload = self.decode(token)
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            raise InvalidToken

        # Compatibilidade temporária: aceita formato legado "user_id:<uuid>"
        if sub.startswith("user_id:"):
            _, sub = sub.split(":", 1)

        if not sub:
            raise InvalidToken

        # coletando perfis
        perfis = payload.get("perfis", [])

        try:
            return str(UUID(sub)), perfis
        except ValueError as exc:
            raise InvalidToken from exc
