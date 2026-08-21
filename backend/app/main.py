import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.predictions import router as prediction_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="IMDB Sentiment Analysis API",
    description="Inference API for the preserved RoBERTa-base IMDB classifier.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health_router)
app.include_router(prediction_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Please provide a valid review of up to 5,000 characters."})


@app.get("/")
def read_root() -> dict[str, str]:
    return {"name": "IMDB Sentiment Analysis", "model": "RoBERTa-base", "status": "running"}
