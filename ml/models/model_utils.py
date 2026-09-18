"""
Model Utilities — Versioning, Serialization, and Metadata Management.

Ensures:
  1. Models and feature lists are saved and loaded consistently.
  2. Training metadata and evaluation metrics are recorded in models/v1/metadata.json.
  3. Strict separation between training artifacts and real-time inference.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np

logger = logging.getLogger("ModelUtils")


def save_model_artifact(
    model: Any,
    filepath: Union[str, Path],
    feature_names: Optional[List[str]] = None,
    metadata_update: Optional[Dict[str, Any]] = None,
    metadata_json_path: Optional[Union[str, Path]] = None,
) -> None:
    """Saves model to disk using joblib and optionally updates the metadata.json registry."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Saved model artifact to: %s", path)

    if metadata_json_path is not None and metadata_update is not None:
        meta_file = Path(metadata_json_path)
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception as e:
                logger.warning("Could not read existing metadata.json: %s", e)

        meta.update(metadata_update)
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()

        if feature_names is not None:
            meta["feature_columns"] = feature_names

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info("Updated model registry metadata: %s", meta_file)


def load_model_artifact(filepath: Union[str, Path]) -> Any:
    """Loads a serialized model from disk."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at: {path}")
    model = joblib.load(path)
    logger.info("Loaded model artifact from: %s", path)
    return model
