from fastapi import APIRouter

from app.api.routes.predictions import get_service
from app.domain.models.prediction import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    service = get_service()
    return HealthResponse(
        status="ok" if service.is_ready() else "degraded",
        model_loaded=service.is_ready(),
        model_path=str(service.model_path),
    )
