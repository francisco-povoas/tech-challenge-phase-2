from typing import List, Optional

# from passlib.context import CryptContext
import bcrypt

from app.shared.ports.hasher import HasherProtocol


class Hasher(HasherProtocol):
    """Implementação concreta de hash usando bcrypt."""

    def hash(self, password: str) -> str:

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed = hashed.decode('utf-8')

        return hashed

    def verify(self, password: str, hashed: str) -> bool:

        result: bool = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))    
        return result
