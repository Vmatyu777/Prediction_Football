from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
from catboost import CatBoostClassifier

from src.api.config import FINAL_APP_METADATA_PATH, PROJECT_ROOT
from src.api.schemas import ModelSummary


@lru_cache(maxsize=1)
def load_metadata() -> dict:
    with FINAL_APP_METADATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_model_summaries() -> list[ModelSummary]:
    metadata = load_metadata()
    return [
        ModelSummary(
            task=model["task"],
            model_type=model["model_type"],
            feature_set=model["feature_set"],
            input_feature_count=model["input_feature_count"],
            threshold=model["threshold"],
            post_processing=model["post_processing"],
        )
        for model in metadata["models"]
    ]


def get_model_config(task: str) -> dict:
    metadata = load_metadata()
    for model_config in metadata["models"]:
        if model_config["task"] == task:
            return model_config
    raise KeyError(f"Unknown model task: {task}")


@lru_cache(maxsize=1)
def load_models() -> dict[str, object]:
    loaded_models = {}
    for model_config in load_metadata()["models"]:
        task = model_config["task"]
        model_path = PROJECT_ROOT / model_config["local_model_path"]
        loaded_models[task] = load_model(model_path, model_config["model_type"])
    return loaded_models


def load_model(model_path: Path, model_type: str) -> object:
    if not model_path.exists():
        raise FileNotFoundError(f"Missing final app model: {model_path}")

    if model_type == "CatBoostClassifier":
        model = CatBoostClassifier()
        model.load_model(model_path)
        return model

    return joblib.load(model_path)
