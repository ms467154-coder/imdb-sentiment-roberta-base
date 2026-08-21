import json
import logging
import re
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.core.config import settings
from app.domain.models.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger("imdb_sentiment.service")


class PredictionServiceError(Exception):
    """Raised when model loading or inference fails."""


class PredictionService:
    def __init__(self) -> None:
        self.model_path = self._resolve_model_path(settings.model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._tokenizer = None
        self._model = None
        self._error: str | None = None
        self._load_model()

    def _resolve_model_path(self, configured_path: str) -> Path:
        path = Path(configured_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[4] / path
        return path.resolve()

    def _load_model(self) -> None:
        try:
            # The checkpoint contains the trained weights but not tokenizer files.
            # The notebook source of truth uses FacebookAI/roberta-base, so reuse
            # that exact tokenizer rather than changing preprocessing or training.
            tokenizer_files = {"tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"}
            has_local_tokenizer = all((self.model_path / filename).exists() for filename in tokenizer_files)
            tokenizer_source = str(self.model_path) if has_local_tokenizer else "FacebookAI/roberta-base"
            self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, local_files_only=has_local_tokenizer)
            self._model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path), local_files_only=True)
            self._model.to(self.device)
            self._model.eval()
            self._error = None
            logger.info("Loaded preserved model from %s with tokenizer %s on %s", self.model_path, tokenizer_source, self.device)
        except Exception as exc:  # pragma: no cover - environment-dependent
            self._error = f"Unable to load model from {self.model_path}: {exc}"
            logger.exception("Model loading failed")

    def is_ready(self) -> bool:
        return self._model is not None and self._tokenizer is not None and self._error is None

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"<.*?>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        if not self.is_ready():
            raise PredictionServiceError(self._error or "Prediction model is not available")

        cleaned_text = self.clean_text(request.text)
        if not cleaned_text:
            raise PredictionServiceError("Review text is empty after preprocessing")

        try:
            inputs = self._tokenizer(
                cleaned_text,
                padding="max_length",
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            with torch.no_grad():
                outputs = self._model(**inputs)

            probabilities = torch.softmax(outputs.logits, dim=-1)[0].cpu().tolist()
            predicted_index = int(torch.argmax(outputs.logits, dim=-1).item())
            sentiment = self._map_prediction(predicted_index)
            confidence = round(float(max(probabilities)), 4)
            return PredictionResponse(
                sentiment=sentiment,
                confidence=confidence,
                cleaned_text=cleaned_text,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("Prediction inference failed")
            raise PredictionServiceError(f"Prediction failed: {exc}") from exc

    def analyze_table(self, file_path: Path, text_column: str | None = None) -> dict[str, object]:
        if not self.is_ready():
            raise PredictionServiceError(self._error or "Prediction model is not available")
        frame = self._read_table(file_path)
        chosen_column = self._choose_text_column(frame, text_column)
        output_rows: list[dict[str, object]] = []
        for index, row in frame.iterrows():
            raw_value = row.get(chosen_column)
            item = {str(key): self._json_safe(value) for key, value in row.to_dict().items()}
            if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)) or not str(raw_value).strip():
                item.update({"prediction": "Skipped", "confidence": None, "error": "No text in selected column"})
            else:
                try:
                    prediction = self.predict(PredictionRequest(text=str(raw_value)))
                    item.update({"prediction": prediction.sentiment, "confidence": prediction.confidence, "error": None})
                except PredictionServiceError as exc:
                    item.update({"prediction": "Error", "confidence": None, "error": str(exc)})
            item["row_number"] = int(index) + 1
            output_rows.append(item)
        return {"file_name": file_path.name, "text_column": chosen_column, "columns": list(output_rows[0].keys()) if output_rows else list(frame.columns), "rows": output_rows, "rows_processed": len(output_rows)}

    def _read_table(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(file_path)
        if suffix == ".json":
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload = payload.get("data", payload)
            return pd.DataFrame(payload if isinstance(payload, list) else [payload])
        raise PredictionServiceError("Unsupported file type. Use CSV, Excel, or JSON.")

    def _choose_text_column(self, frame: pd.DataFrame, requested: str | None) -> str:
        if requested and requested in frame.columns:
            return requested
        names = {str(column).lower(): str(column) for column in frame.columns}
        for preferred in ("review", "text", "sentence", "comment", "content"):
            if preferred in names:
                return names[preferred]
        string_columns = frame.select_dtypes(include=["object", "string"]).columns
        if len(string_columns):
            return str(string_columns[0])
        raise PredictionServiceError("No text column was found. Select a column containing review sentences.")

    @staticmethod
    def _json_safe(value: object) -> object:
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            return value.item()
        return value

    def _map_prediction(self, predicted_index: int) -> str:
        label_map = getattr(self._model.config, "id2label", None)
        if isinstance(label_map, dict):
            label_name = str(label_map.get(predicted_index, "")).lower()
            if "pos" in label_name or "good" in label_name:
                return "Positive"
            if "neg" in label_name or "bad" in label_name:
                return "Negative"
        return "Positive" if predicted_index == 1 else "Negative"
