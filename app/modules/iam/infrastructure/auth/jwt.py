"""Compatibilidade: JWT foi movido para `app.shared.infra.security.jwt`."""

from app.shared.infra.security.jwt import InvalidToken, JWTProvider

__all__ = ["JWTProvider", "InvalidToken"]
