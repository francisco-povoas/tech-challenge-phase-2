from fastapi import APIRouter

router = APIRouter()


@router.get("/health-check", summary="Health check da API")
async def health_check() -> dict[str, str]:
    return {"status": "I'm ok!"}
