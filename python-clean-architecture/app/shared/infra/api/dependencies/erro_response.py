# presentation/http/schemas/common.py

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str