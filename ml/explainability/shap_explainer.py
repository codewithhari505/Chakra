"""
Explainable AI (XAI) Engine — SHAP Explanations — Phase 11.

Generates local and global feature-attribution explanations for AML decisions:
  - Local Explanations: Exactly which behavioral signals drove suspicion for a specific transaction
  - Directional Impact: Distinguishes features increasing risk (+) vs lowering risk (-)
  - Fallback / High-Speed Heuristic: Rapid linear attribution when SHAP background initialization is deferred

Adheres strictly to investigator transparency:
  - Explanations are empirical ML attributions, not statements of guilt.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ml.models.supervised_model import AML_FEATURE_COLUMNS

logger = logging.getLogger("SHAPExplainer")


@dataclass
class FeatureContribution:
    feature: str
    feature_value: float
    contribution: float   # Positive = increases suspicion risk; Negative = decreases suspicion risk
    impact_direction: str # "INCREASES_RISK" | "DECREASES_RISK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "value": round(self.feature_value, 2),
            "contribution": round(self.contribution, 4),
            "impact": self.impact_direction,
        }


class AMLTransactionExplainer:
    """
    Computes local feature attribution explanations for supervised AML models.
    Supports TreeExplainer with high-speed fallback for real-time transactions.
    """

    def __init__(self, model: Any = None, feature_names: Optional[List[str]] = None):
        self.model = model
        self.feature_names = feature_names or AML_FEATURE_COLUMNS
        self.tree_explainer = None
        self._init_shap()

    def _init_shap(self):
        """Initializes SHAP TreeExplainer if shap library is available."""
        if self.model is not None:
            try:
                import shap
                # Extract inner model if wrapped
                inner = getattr(self.model, "model", self.model)
                self.tree_explainer = shap.TreeExplainer(inner)
                logger.info("SHAP TreeExplainer initialized successfully.")
            except Exception as e:
                logger.warning("Could not initialize SHAP TreeExplainer: %s. Using tree importance fallback.", e)
                self.tree_explainer = None

    def explain_transaction(
        self,
        transaction_features: Union[pd.Series, Dict[str, Any], pd.DataFrame],
        top_n: int = 5
    ) -> List[FeatureContribution]:
        """
        Explains an individual transaction prediction.
        Returns top N features with their signed impact on risk.
        """
        if isinstance(transaction_features, dict):
            df_single = pd.DataFrame([transaction_features])
        elif isinstance(transaction_features, pd.Series):
            df_single = pd.DataFrame([transaction_features.to_dict()])
        else:
            df_single = transaction_features.copy()

        # Ensure all required features are present
        for col in self.feature_names:
            if col not in df_single.columns:
                df_single[col] = 0.0

        X = df_single[self.feature_names].fillna(0.0).values
        feature_vals = X[0]

        # 1. Primary path: TreeSHAP
        if self.tree_explainer is not None:
            try:
                shap_vals = self.tree_explainer.shap_values(X)
                # If binary classification returns list of arrays [class_0, class_1]
                if isinstance(shap_vals, list) and len(shap_vals) == 2:
                    vals = shap_vals[1][0]
                elif isinstance(shap_vals, np.ndarray):
                    if shap_vals.ndim == 3:
                        vals = shap_vals[0, :, 1]
                    elif shap_vals.ndim == 2:
                        vals = shap_vals[0]
                    else:
                        vals = shap_vals
                else:
                    vals = np.zeros(len(self.feature_names))

                ranked_indices = np.argsort(np.abs(vals))[::-1]

                contributions = []
                for idx in ranked_indices[:top_n]:
                    contrib = float(vals[idx])
                    contributions.append(FeatureContribution(
                        feature=self.feature_names[idx],
                        feature_value=float(feature_vals[idx]),
                        contribution=contrib,
                        impact_direction="INCREASES_RISK" if contrib > 0 else "DECREASES_RISK",
                    ))
                return contributions
            except Exception as e:
                logger.warning("Error running TreeSHAP: %s. Falling back to feature weighting.", e)

        # 2. Fallback path: Model feature importances * standardized deviation
        return self._heuristic_explanation(feature_vals, top_n)

    def _heuristic_explanation(self, feature_vals: np.ndarray, top_n: int) -> List[FeatureContribution]:
        """Calculates fast attribution using feature importances and magnitude deviations."""
        importances = getattr(self.model, "get_feature_importances", None)
        if callable(importances):
            imp_list = importances(top_n=len(self.feature_names))
            imp_dict = {f["feature"]: f["importance"] for f in imp_list}
        else:
            imp_dict = {f: 1.0 / len(self.feature_names) for f in self.feature_names}

        scores = []
        for idx, feat in enumerate(self.feature_names):
            val = float(feature_vals[idx])
            weight = imp_dict.get(feat, 0.01)
            # Higher values in risk features (amounts, counts, ratios) push risk upward
            contrib = float(weight * np.log1p(max(0.0, val)))
            scores.append((feat, val, contrib))

        scores = sorted(scores, key=lambda x: abs(x[2]), reverse=True)
        return [
            FeatureContribution(
                feature=feat,
                feature_value=val,
                contribution=round(contrib, 4),
                impact_direction="INCREASES_RISK" if contrib > 0 else "DECREASES_RISK",
            )
            for feat, val, contrib in scores[:top_n]
        ]
