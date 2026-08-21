import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.application.services.prediction_service import PredictionService, PredictionServiceError
from app.domain.models.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger("imdb_sentiment.predictions")
router = APIRouter()
service = PredictionService()


@router.post("/predict", response_model=PredictionResponse)
def create_prediction(request: PredictionRequest) -> PredictionResponse:
    try:
        return service.predict(request)
    except PredictionServiceError as exc:
        logger.warning("Prediction unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="The sentiment model is currently unavailable.") from exc


@router.post("/batch-predict")
async def batch_predict(file: UploadFile = File(...), text_column: str | None = Form(default=None)) -> dict[str, object]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls", ".json"}:
        raise HTTPException(status_code=400, detail="Upload a CSV, Excel (.xlsx/.xls), or JSON file.")
    try:
        content = await file.read()
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        return service.analyze_table(temporary_path, text_column=text_column)
    except PredictionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Batch prediction failed")
        raise HTTPException(status_code=400, detail="The uploaded file could not be analyzed.") from exc
    finally:
        if "temporary_path" in locals():
            temporary_path.unlink(missing_ok=True)


def get_service() -> PredictionService:
    return service
