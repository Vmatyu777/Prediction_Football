from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.config import FINAL_APP_METADATA_PATH
from src.api.database.init_db import init_db
from src.api.database.models import Metric, Model, ModelMetric, ModelType
from src.api.database.session import SessionLocal


MODEL_VERSION = "final_app_v1"
FALLBACK_TRAINED_AT = datetime(2026, 5, 25)

MODEL_DISPLAY_NAMES = {
    "outcome": "Outcome",
    "btts": "BTTS",
    "over25": "Over2.5",
    "corners_over95": "Corners Over9.5",
    "yellow_cards_over35": "Yellow Cards Over3.5",
    "exact_score_home_goals": "Exact Score Home Goals",
    "exact_score_away_goals": "Exact Score Away Goals",
}

FINAL_TEST_METRICS = {
    "outcome": {
        "primary_metric": "macro_f1",
        "metrics": {
            "accuracy": 0.5111,
            "macro_f1": 0.4867,
            "balanced_accuracy": 0.4861,
        },
    },
    "btts": {
        "primary_metric": "balanced_accuracy",
        "metrics": {
            "accuracy": 0.5437,
            "balanced_accuracy": 0.5335,
            "f1": 0.6042,
        },
    },
    "over25": {
        "primary_metric": "balanced_accuracy",
        "metrics": {
            "accuracy": 0.5958,
            "balanced_accuracy": 0.5875,
            "f1": 0.6516,
        },
    },
    "corners_over95": {
        "primary_metric": "balanced_accuracy",
        "metrics": {
            "accuracy": 0.5563,
            "balanced_accuracy": 0.5560,
            "f1": 0.5150,
        },
    },
    "yellow_cards_over35": {
        "primary_metric": "balanced_accuracy",
        "metrics": {
            "accuracy": 0.5512,
            "balanced_accuracy": 0.5559,
            "f1": 0.5731,
        },
    },
    "exact_score_home_goals": {
        "primary_metric": "mae",
        "metrics": {
            "mae": 0.8948,
            "rmse": 1.1809,
        },
    },
    "exact_score_away_goals": {
        "primary_metric": "mae",
        "metrics": {
            "mae": 0.8399,
            "rmse": 1.1015,
        },
    },
}


def load_final_model_metadata() -> list[dict]:
    with FINAL_APP_METADATA_PATH.open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    return metadata["models"]


def empty_summary() -> dict[str, int]:
    return {
        "models_inserted": 0,
        "models_found": 0,
        "metrics_inserted": 0,
        "metrics_found": 0,
        "model_metrics_inserted": 0,
        "model_metrics_found": 0,
        "model_types_inserted": 0,
        "model_types_found": 0,
    }


def final_model_trained_at(local_model_path: str) -> datetime:
    model_path = PROJECT_ROOT / local_model_path
    if model_path.exists():
        return datetime.fromtimestamp(model_path.stat().st_mtime)
    return FALLBACK_TRAINED_AT


def decimal_metric(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def get_or_create_model_type(db: Session, summary: dict[str, int], name: str) -> ModelType:
    model_type = db.query(ModelType).filter(ModelType.name == name).first()
    if model_type:
        summary["model_types_found"] += 1
        return model_type

    model_type = ModelType(name=name)
    db.add(model_type)
    db.flush()
    summary["model_types_inserted"] += 1
    return model_type


def get_or_create_metric(db: Session, summary: dict[str, int], name: str) -> Metric:
    metric = db.query(Metric).filter(Metric.name == name).first()
    if metric:
        summary["metrics_found"] += 1
        return metric

    metric = Metric(name=name)
    db.add(metric)
    db.flush()
    summary["metrics_inserted"] += 1
    return metric


def get_or_create_model(
    db: Session,
    summary: dict[str, int],
    model_config: dict,
    model_type_id: int,
) -> Model:
    model = db.query(Model).filter(Model.file_path == model_config["local_model_path"]).first()
    if model:
        summary["models_found"] += 1
        return model

    model = Model(
        name=MODEL_DISPLAY_NAMES[model_config["task"]],
        version=MODEL_VERSION,
        trained_at=final_model_trained_at(model_config["local_model_path"]),
        file_path=model_config["local_model_path"],
        model_type_id=model_type_id,
    )
    db.add(model)
    db.flush()
    summary["models_inserted"] += 1
    return model


def get_or_create_model_metric(
    db: Session,
    summary: dict[str, int],
    model_id: int,
    metric_id: int,
    metric_value: Decimal,
    is_primary: bool,
) -> None:
    existing = (
        db.query(ModelMetric)
        .filter(ModelMetric.model_id == model_id, ModelMetric.metric_id == metric_id)
        .first()
    )
    if existing:
        summary["model_metrics_found"] += 1
        return

    db.add(
        ModelMetric(
            model_id=model_id,
            metric_id=metric_id,
            metric_value=metric_value,
            is_primary=is_primary,
        )
    )
    summary["model_metrics_inserted"] += 1


def seed_final_models() -> dict[str, int]:
    init_db()
    summary = empty_summary()

    with SessionLocal() as db:
        for model_config in load_final_model_metadata():
            task = model_config["task"]
            if task not in FINAL_TEST_METRICS:
                continue

            model_type = get_or_create_model_type(db, summary, model_config["model_type"])
            model = get_or_create_model(db, summary, model_config, model_type.id)
            task_metrics = FINAL_TEST_METRICS[task]
            primary_metric = task_metrics["primary_metric"]

            for metric_name, metric_value in task_metrics["metrics"].items():
                metric = get_or_create_metric(db, summary, metric_name)
                get_or_create_model_metric(
                    db=db,
                    summary=summary,
                    model_id=model.id,
                    metric_id=metric.id,
                    metric_value=decimal_metric(metric_value),
                    is_primary=metric_name == primary_metric,
                )

        db.commit()

    return summary


def main() -> None:
    summary = seed_final_models()
    print("Final model metadata seed completed.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
