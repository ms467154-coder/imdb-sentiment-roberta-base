from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="An IMDB-style movie review")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Review text cannot be empty")
        return cleaned


class PredictionResponse(BaseModel):
    sentiment: str
    confidence: float | None = None
    model: str = "RoBERTa-base"
    cleaned_text: str | None = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str
