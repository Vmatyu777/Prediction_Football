from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


OUTCOME_LABELS = ["H", "D", "A"]


def evaluate_classifier(
    *,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict[str, float | str]:
    report = classification_report(
        y_true,
        y_pred,
        labels=OUTCOME_LABELS,
        output_dict=True,
        zero_division=0,
    )
    return {
        "model": model_name,
        "split": split_name,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "home_recall": report["H"]["recall"],
        "draw_recall": report["D"]["recall"],
        "away_recall": report["A"]["recall"],
    }


def classification_report_frame(
    *,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> pd.DataFrame:
    report = classification_report(
        y_true,
        y_pred,
        labels=OUTCOME_LABELS,
        output_dict=True,
        zero_division=0,
    )
    frame = pd.DataFrame(report).transpose().reset_index(names="label")
    frame.insert(0, "split", split_name)
    frame.insert(0, "model", model_name)
    return frame


def save_confusion_matrix_figure(
    *,
    y_true: pd.Series,
    y_pred: pd.Series,
    output_path: Path,
    title: str,
) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=OUTCOME_LABELS)

    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(OUTCOME_LABELS)), OUTCOME_LABELS)
    ax.set_yticks(range(len(OUTCOME_LABELS)), OUTCOME_LABELS)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title(title)

    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            ax.text(
                column_index,
                row_index,
                str(value),
                ha="center",
                va="center",
                color="white" if value > matrix.max() / 2 else "black",
            )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def confusion_matrix_frame(
    *,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> pd.DataFrame:
    matrix = confusion_matrix(y_true, y_pred, labels=OUTCOME_LABELS)
    rows = []
    for true_index, true_label in enumerate(OUTCOME_LABELS):
        for pred_index, pred_label in enumerate(OUTCOME_LABELS):
            rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "true_label": true_label,
                    "predicted_label": pred_label,
                    "count": int(matrix[true_index, pred_index]),
                }
            )
    return pd.DataFrame(rows)
