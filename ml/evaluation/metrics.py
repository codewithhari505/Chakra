"""
Model Evaluation Metrics — Phase 6.

Computes precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix,
and financial fraud metrics with special handling for class imbalance.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


@dataclass
class EvaluationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    confusion_mat: List[List[int]]
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "confusion_matrix": self.confusion_mat,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
        }

    def summary(self, model_name: str = "Classifier") -> str:
        return (
            f"\n================= {model_name} Evaluation Summary =================\n"
            f"  Accuracy  : {self.accuracy:.4f}\n"
            f"  Precision : {self.precision:.4f}  (Low False Positive Rate)\n"
            f"  Recall    : {self.recall:.4f}  (High Detection of Illicit Flows)\n"
            f"  F1-Score  : {self.f1:.4f}\n"
            f"  ROC-AUC   : {self.roc_auc:.4f}\n"
            f"  PR-AUC    : {self.pr_auc:.4f}  (Crucial for Rare AML Class)\n"
            f"  Confusion Matrix:\n"
            f"    TN={self.true_negatives} | FP={self.false_positives}\n"
            f"    FN={self.false_negatives} | TP={self.true_positives}\n"
            f"====================================================================\n"
        )


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None
) -> EvaluationMetrics:
    """Computes comprehensive evaluation metrics comparing ground truth to model predictions."""
    y_true_arr = np.asarray(y_true, dtype=int)
    y_pred_arr = np.asarray(y_pred, dtype=int)

    cm = confusion_matrix(y_true_arr, y_pred_arr)
    tn, fp, fn, tp = cm.ravel()

    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))
    acc = float((tp + tn) / (tp + tn + fp + fn)) if (tp + tn + fp + fn) > 0 else 0.0

    if y_prob is not None and len(np.unique(y_true_arr)) > 1:
        roc = float(roc_auc_score(y_true_arr, y_prob))
        pr_auc = float(average_precision_score(y_true_arr, y_prob))
    else:
        roc = 0.0
        pr_auc = 0.0

    return EvaluationMetrics(
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1=f1,
        roc_auc=roc,
        pr_auc=pr_auc,
        confusion_mat=cm.tolist(),
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
    )
