import json
from typing import Any, Dict

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def adapt_type_error(message: str) -> str:
    return message[message.index("missing"):].replace("positional argument", "field")


def _adapt_message(error: Dict[str, str]) -> str:
    msg = error.get("msg", "")
    if msg and error.get("type") == "type_error":
        return adapt_type_error(msg)
    return msg


def _to_json_safe(value: Any) -> Any:
    """Converte recursivamente valores não-serializáveis em string."""
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        error.update({"msg": _adapt_message(error)})
        errors.append(error)
    return JSONResponse({"detail": _to_json_safe(errors)}, status_code=422)


# Assegura que erros nao tratados sejam convertidos em respostas JSON genéricas, sem vazar detalhes do erro ou dados de entrada.
def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."},
    )
