# Model artifacts

The repository’s trained checkpoint is intentionally kept outside the GitHub source release because the weight and optimizer files exceed normal GitHub file limits. The application expects the following local path:

```text
results/checkpoint-2480/
```

The inference service requires the trained `config.json` and `model.safetensors`. The original training directory also contains optimizer, scheduler, scaler, RNG, and trainer-state files for research reproducibility; those files are not required for inference. The tokenizer is loaded from the exact notebook source, `FacebookAI/roberta-base`, when tokenizer files are absent from the checkpoint.

To restore local inference, copy the preserved `checkpoint-2480` directory from the original project into the cloned repository’s `results/` directory, then start the backend and confirm:

```text
GET http://127.0.0.1:8000/health
```

A healthy response reports `model_loaded: true`. The notebook, dataset, and model-training record remain part of the original research project and should be retained for reproducibility and audit purposes.
