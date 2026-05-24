from __future__ import annotations

import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FINAL_APP_DIR = PROJECT_ROOT / "models" / "final_app"
METADATA_PATH = PROJECT_ROOT / "configs" / "final_app_models.json"

EXACT_SCORE_CLIP_RANGE = [0, 6]
RECONCILIATION_PRIORITY_ORDER = ["outcome", "btts", "over25", "exact_score"]

FINAL_MODELS = [
    {
        "task": "outcome",
        "model_type": "LogisticRegression",
        "feature_set": "v1_only",
        "input_feature_count": 36,
        "output": "Home Win / Draw / Away Win",
        "threshold": None,
        "post_processing": "default_argmax",
        "source_model_path": "models/outcome/logistic_regression_controlled_best.joblib",
        "local_model_path": "models/final_app/outcome_model.joblib",
    },
    {
        "task": "btts",
        "model_type": "LogisticRegression",
        "feature_set": "v1_only",
        "input_feature_count": 36,
        "output": "BTTS Yes / No",
        "threshold": 0.5,
        "post_processing": "threshold_0_50",
        "source_model_path": "models/btts/v1_only__logistic_regression.joblib",
        "local_model_path": "models/final_app/btts_model.joblib",
    },
    {
        "task": "over25",
        "model_type": "CatBoostClassifier",
        "feature_set": "v1_only",
        "input_feature_count": 36,
        "output": "Over2.5 Yes / No",
        "threshold": 0.5,
        "post_processing": "threshold_0_50",
        "source_model_path": "models/over25/v1_only__catboost_classifier.cbm",
        "local_model_path": "models/final_app/over25_model.cbm",
    },
    {
        "task": "corners_over95",
        "model_type": "CatBoostClassifier",
        "feature_set": "v1_only",
        "input_feature_count": 36,
        "output": "Corners Over9.5 Yes / No",
        "threshold": 0.5,
        "post_processing": "threshold_0_50",
        "source_model_path": "models/corners/v1_only__catboost_classifier.cbm",
        "local_model_path": "models/final_app/corners_over95_model.cbm",
    },
    {
        "task": "yellow_cards_over35",
        "model_type": "LogisticRegression",
        "feature_set": "v1_yellow_related",
        "input_feature_count": 54,
        "output": "Yellow Cards Over3.5 Yes / No",
        "threshold": 0.5,
        "post_processing": "threshold_0_50",
        "source_model_path": "models/yellow_cards/logistic_regression_controlled_best.joblib",
        "local_model_path": "models/final_app/yellow_cards_over35_model.joblib",
    },
    {
        "task": "exact_score_home_goals",
        "model_type": "Ridge",
        "feature_set": "v1_score_related",
        "input_feature_count": 30,
        "output": "predicted home goals",
        "threshold": None,
        "post_processing": "round_and_clip_0_6",
        "source_model_path": "models/exact_score/v1_score_related__ridge_regression__home_goals.joblib",
        "local_model_path": "models/final_app/exact_score_home_goals_model.joblib",
    },
    {
        "task": "exact_score_away_goals",
        "model_type": "Ridge",
        "feature_set": "v1_score_related",
        "input_feature_count": 30,
        "output": "predicted away goals",
        "threshold": None,
        "post_processing": "round_and_clip_0_6",
        "source_model_path": "models/exact_score/v1_score_related__ridge_regression__away_goals.joblib",
        "local_model_path": "models/final_app/exact_score_away_goals_model.joblib",
    },
]


def build_metadata() -> dict:
    models_metadata = []
    for model_config in FINAL_MODELS:
        model_metadata = dict(model_config)
        model_metadata["tracked_by_git"] = False
        models_metadata.append(model_metadata)

    return {
        "model_package": {
            "local_directory": "models/final_app",
            "model_files_tracked_by_git": False,
            "metadata_tracked_by_git": True,
            "intended_consumer": "backend_api",
        },
        "reconciliation": {
            "priority_order": RECONCILIATION_PRIORITY_ORDER,
            "module": "src/postprocessing/consistency_layer.py",
            "logic": "priority_based_rule_reconciliation",
            "exact_score_clip_range": EXACT_SCORE_CLIP_RANGE,
        },
        "models": models_metadata,
    }


def copy_final_models() -> tuple[list[str], list[str], list[str]]:
    FINAL_APP_DIR.mkdir(parents=True, exist_ok=True)
    copied_models: list[str] = []
    missing_models: list[str] = []
    failed_copies: list[str] = []

    for model_config in FINAL_MODELS:
        source_path = PROJECT_ROOT / model_config["source_model_path"]
        target_path = PROJECT_ROOT / model_config["local_model_path"]

        if not source_path.exists():
            missing_models.append(model_config["source_model_path"])
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

        if target_path.exists():
            copied_models.append(model_config["task"])
        else:
            failed_copies.append(model_config["local_model_path"])

    return copied_models, missing_models, failed_copies


def write_metadata() -> None:
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(build_metadata(), indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    copied_models, missing_models, failed_copies = copy_final_models()
    write_metadata()

    print("Final app model package preparation summary")
    print(f"Copied models: {len(copied_models)}")
    for task in copied_models:
        print(f"  - {task}")

    print(f"Missing source models: {len(missing_models)}")
    for model_path in missing_models:
        print(f"  - {model_path}")

    print(f"Failed copied model checks: {len(failed_copies)}")
    for model_path in failed_copies:
        print(f"  - {model_path}")

    print(f"Updated metadata path: {METADATA_PATH.relative_to(PROJECT_ROOT)}")

    if missing_models or failed_copies:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
