# IMDB Sentiment Analysis — RoBERTa-base

A production-oriented full-stack application around an existing IMDB sentiment classifier fine-tuned with **RoBERTa-base**. The project preserves the original notebook, dataset, checkpoints, preprocessing, tokenizer settings, and evaluation record while adding a focused React interface and FastAPI inference service.

> **The ML/NLP implementation is the source of truth.** The application productizes it; it does not retrain, fine-tune, replace, or “improve” the model.

## What it does

Enter an IMDB-style review and receive the saved model’s **Positive** or **Negative** sentiment prediction and model-derived confidence. The interface also documents the actual preprocessing and inference flow, including HTML removal, whitespace normalization, RoBERTa tokenization, padded/truncated sequences of length 256, and the saved best checkpoint.

## Repository structure

```text
.
├── IMDB Dataset.csv
├── IMDB Sentiment Analysis.ipynb   # protected research source of truth
├── results/                         # protected checkpoints and trainer state
├── backend/
│   └── app/
│       ├── api/routes/              # health and prediction endpoints
│       ├── application/services/    # one-time model loading and inference
│       ├── core/                    # environment configuration
│       └── domain/models/           # typed request/response schemas
├── frontend/
│   └── src/
│       ├── services/api.ts          # typed API client
│       ├── App.tsx                  # product pages and interactions
│       └── styles/index.css         # crimson/cream design system
└── docs/
    └── repository-audit.md
```

## Local development

The commands below are written for **Windows PowerShell** and assume the repository is located at:

```text
C:\Users\AbdElhalk\OneDrive\Desktop\NLP &LLMs Projects\IMDB Sentiment Analysis RoBERTa-base
```

Because the parent path contains `&`, use `Set-Location -LiteralPath` rather than an unquoted `cd` command.

### Backend — Terminal 1

Open the first terminal and run:

```powershell
$project = Get-ChildItem "$env:USERPROFILE\OneDrive\Desktop\NLP *" -Directory | Get-ChildItem -Directory | Where-Object Name -like "IMDB*" | Select-Object -First 1
Set-Location -LiteralPath (Join-Path $project.FullName "backend")
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If the backend virtual environment does not exist yet, run this once from the project folder:

```powershell
Set-Location -LiteralPath (Join-Path $project.FullName "backend")
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`, and its health endpoint is `http://127.0.0.1:8000/health`. The backend uses the exact `FacebookAI/roberta-base` tokenizer source from the notebook when tokenizer files are not bundled inside the saved checkpoint, while loading the preserved trained weights from `results/checkpoint-2480`.

### Batch file analysis

The application accepts `.csv`, `.xlsx`, `.xls`, and `.json` files through `POST /api/batch-predict`. The API auto-detects a text column named `review`, `text`, `sentence`, `comment`, or `content`, or accepts a selected `text_column` form field. It analyzes every non-empty row and returns the original row data plus `prediction`, `confidence`, `error`, and `row_number`. Empty rows are retained and marked as `Skipped` rather than silently discarded.

Example request with Windows curl:

```powershell
curl.exe -X POST -F "file=@C:\path\to\reviews.csv" http://127.0.0.1:8000/api/batch-predict
```

The frontend’s **Batch files** tab supports column selection, per-row result tables, and downloading the results as CSV or JSON.

### Frontend — Terminal 2

Open a second terminal and run:

```powershell
$project = Get-ChildItem "$env:USERPROFILE\OneDrive\Desktop\NLP *" -Directory | Get-ChildItem -Directory | Where-Object Name -like "IMDB*" | Select-Object -First 1
Set-Location -LiteralPath (Join-Path $project.FullName "frontend")
npm install
npm run dev -- --host 127.0.0.1
```

The frontend preview will normally be available at `http://127.0.0.1:5173`.

### Frontend build preview

To create and preview a production build instead of using the development server:

```powershell
Set-Location -LiteralPath (Join-Path $project.FullName "frontend")
npm run build
npm run preview -- --host 127.0.0.1
```

Set `VITE_API_BASE_URL` when the API is not running at `http://localhost:8000`.

The frontend includes Overview, Sentiment Analyzer, Model / Architecture, Evaluation, and Documentation views. The application is responsive, keyboard navigable, and designed around a dark-crimson and warm off-white visual identity.

## API

`POST /api/predict` accepts `{ "text": "This movie was fantastic." }` and returns the model-derived sentiment, confidence, model name, and cleaned text. `GET /health` reports whether the preserved tokenizer and model loaded successfully. Validation rejects empty reviews and inputs longer than 5,000 characters.

## ML integration contract

The backend intentionally mirrors the notebook’s inference behavior. It removes HTML tags, normalizes whitespace, uses the saved tokenizer with `padding="max_length"`, `truncation=True`, and `max_length=256`, then runs the saved sequence-classification model in evaluation mode. The service loads the model once rather than once per request.

No dataset-upload or batch-processing surface is included in the product application because the brief is focused on the IMDB review experience. The original dataset and all research artifacts remain in the repository as protected ML inputs and records.

## Verification

The original notebook and checkpoint artifacts must remain unchanged. Backend tests should verify valid, empty, oversized, unavailable-model, and response-schema paths. Frontend verification should cover empty state, loading state, successful prediction, error state, responsive navigation, and keyboard focus behavior.

## Future improvements

Possible extensions include adding a deployment configuration, exposing source-backed evaluation charts, and adding a model-card view once those artifacts are made available in a stable machine-readable form. Any future change must preserve the original ML/NLP contract.

## Repository artifact policy

The GitHub source release intentionally excludes the local `results/checkpoint-2480` binary weights and optimizer state because the preserved model files are larger than standard GitHub file limits. The application still uses that checkpoint locally. To run inference after cloning, restore the checkpoint directory from the original project or place an equivalent trained checkpoint at `results/checkpoint-2480`; the backend will reuse the notebook-compatible `FacebookAI/roberta-base` tokenizer when tokenizer files are not bundled with the checkpoint. See `docs/model-artifacts.md` for the exact expected files and local setup.
