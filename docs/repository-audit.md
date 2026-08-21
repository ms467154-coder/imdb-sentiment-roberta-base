# Repository Audit

## Source of truth

The notebook `IMDB Sentiment Analysis.ipynb` and the saved checkpoints under `results/` are the protected ML/NLP core. The notebook performs HTML-tag removal with `clean_text`, whitespace normalization with `clean_spaces`, and applies both transformations before tokenization.

The preserved inference contract is:

1. Clean the input using the notebook functions.
2. Use the saved RoBERTa tokenizer.
3. Tokenize with `padding="max_length"`, `truncation=True`, and `max_length=256`.
4. Run the saved sequence-classification model in evaluation mode.
5. Return the model-derived sentiment label and confidence.

The best saved checkpoint is `results/checkpoint-2480`, as recorded by the training state. No retraining, fine-tuning, architecture change, tokenizer change, preprocessing change, dataset change, or metric recalculation is permitted.

## Classification

| Classification | Items | Decision |
|---|---|---|
| Keep: ML/NLP core | `IMDB Dataset.csv`, `IMDB Sentiment Analysis.ipynb`, `results/` | Preserve unchanged. |
| Rebuild: application | `frontend/src/App.tsx`, legacy Salem Predictions UI, dataset-upload workflow, current prediction API surface | Replace with the focused review-analysis product. |
| Keep/adapt: infrastructure | `frontend/` Vite scaffold, FastAPI package layout, shared dependencies | Reuse where useful, but remove obsolete application behavior. |
| Keep/update: documentation | `README.md`, `docs/` | Rewrite to describe the actual project and application. |
| Review | Existing environment and generated build/cache folders | Exclude from source changes; do not treat generated output as authored source. |

## Integration boundary

The backend will own one model service that loads the tokenizer and `results/checkpoint-2480` once at startup/import, applies the exact notebook cleaning/tokenization behavior, performs inference, and returns structured JSON. The frontend will call a dedicated API service rather than embedding request logic in page components.

## Safety notes

The legacy backend currently tokenizes with `max_length=512` and does not apply the notebook cleaning functions. That behavior must not be retained as the production inference path. Dataset upload and processing are outside the focused product brief and will be removed from the application surface, while the original dataset remains protected as ML research input.
