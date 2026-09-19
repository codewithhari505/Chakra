"""
Unified Risk Scoring Engine — Phase 10 & 11.

Computes a calibrated composite risk score (0 to 100) combining four independent analytical pillars:
  1. Supervised Machine Learning Score (XGBoost / Random Forest)  [Default: 40%]
  2. Unsupervised Anomaly Detection Score (Isolation Forest)       [Default: 20%]
  3. Rule-Based Indicators & Statutory PMLA/RBI Checks             [Default: 20%]
  4. Network Topology & Graph Risk Score (NetworkX)                [Default: 20%]

Phase 11 Extension:
  - Local Explainable AI (XAI) feature attributions via TreeSHAP
  - Identifies specific transaction attributes driving model risk up (+) or down (-)
"""

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from ml.rules.rule_engine import AMLRuleEngine, RuleEvaluation, RuleResult
from ml.models.supervised_model import AMLXGBoostModel, AMLRandomForestModel, AML_FEATURE_COLUMNS
from ml.models.anomaly_model import AMLIsolationForestModel
from ml.explainability.shap_explainer import AMLTransactionExplainer

logger = logging.getLogger("RiskEngine")


@dataclass
class UnifiedRiskReport:
    """Comprehensive multi-pillar risk evaluation and explainability report for an investigator."""
    transaction_id: str
    final_risk_score: float      # 0.0 to 100.0
    risk_level: str              # LOW | MEDIUM | HIGH | CRITICAL
    ml_score: float              # 0.0 to 100.0
    anomaly_score: float         # 0.0 to 100.0
    rule_score: float            # 0.0 to 100.0
    network_score: float         # 0.0 to 100.0
    weights_used: Dict[str, float]
    triggered_rules: List[Dict[str, Any]]
    feature_attributions: List[Dict[str, Any]] = field(default_factory=list)
    explanation_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "final_risk_score": round(self.final_risk_score, 1),
            "risk_level": self.risk_level,
            "component_scores": {
                "ml_score": round(self.ml_score, 1),
                "anomaly_score": round(self.anomaly_score, 1),
                "rule_score": round(self.rule_score, 1),
                "network_score": round(self.network_score, 1),
            },
            "weights_used": self.weights_used,
            "triggered_rules": self.triggered_rules,
            "feature_attributions": self.feature_attributions,
            "explanation_summary": self.explanation_summary,
        }


class UnifiedRiskScoringEngine:
    """
    Combines supervised learning, unsupervised anomaly detection,
    heuristic compliance rules, graph topology metrics, and SHAP explainability.
    """

    def __init__(
        self,
        weight_ml: Optional[float] = None,
        weight_anomaly: Optional[float] = None,
        weight_rules: Optional[float] = None,
        weight_network: Optional[float] = None,
        supervised_model_path: Optional[str] = None,
        anomaly_model_path: Optional[str] = None,
    ):
        settings = get_settings()

        self.w_ml = weight_ml if weight_ml is not None else settings.risk_weight_ml
        self.w_anom = weight_anomaly if weight_anomaly is not None else settings.risk_weight_anomaly
        self.w_rule = weight_rules if weight_rules is not None else settings.risk_weight_rules
        self.w_net = weight_network if weight_network is not None else settings.risk_weight_network

        total_w = self.w_ml + self.w_anom + self.w_rule + self.w_net
        if total_w > 0:
            self.w_ml /= total_w
            self.w_anom /= total_w
            self.w_rule /= total_w
            self.w_net /= total_w

        self.rule_engine = AMLRuleEngine()

        self.supervised_model = None
        self.anomaly_model = None
        self.explainer = None

        xgb_path = Path("./models/v1/xgboost_classifier.pkl")
        rf_path = Path(supervised_model_path or settings.fraud_classifier_path)
        anom_path = Path(anomaly_model_path or settings.anomaly_detector_path)

        if xgb_path.exists():
            try:
                self.supervised_model = AMLXGBoostModel.load(xgb_path)
                logger.info("Loaded XGBoost as primary supervised classifier.")
            except Exception as e:
                logger.warning("Could not load XGBoost: %s", e)

        if self.supervised_model is None and rf_path.exists():
            try:
                self.supervised_model = AMLRandomForestModel.load(rf_path)
                logger.info("Loaded Random Forest as primary supervised classifier.")
            except Exception as e:
                logger.warning("Could not load Random Forest: %s", e)

        if anom_path.exists():
            try:
                self.anomaly_model = AMLIsolationForestModel.load(anom_path)
                logger.info("Loaded Isolation Forest anomaly detector.")
            except Exception as e:
                logger.warning("Could not load Isolation Forest: %s", e)

        # Initialize SHAP explainer on loaded supervised model
        if self.supervised_model is not None:
            try:
                self.explainer = AMLTransactionExplainer(model=self.supervised_model)
            except Exception as e:
                logger.warning("Could not initialize SHAP explainer: %s", e)

    def calculate_risk(
        self,
        transaction_data: Union[pd.Series, Dict[str, Any]],
        network_score: float = 0.0,
        include_attributions: bool = True
    ) -> UnifiedRiskReport:
        """
        Evaluates an individual transaction across all four pillars and returns a UnifiedRiskReport.
        """
        settings = get_settings()
        row_dict = transaction_data.to_dict() if hasattr(transaction_data, "to_dict") else dict(transaction_data)
        if "transaction_amount" not in row_dict and "amount" in row_dict:
            row_dict["transaction_amount"] = float(row_dict["amount"])
        if "amount" not in row_dict and "transaction_amount" in row_dict:
            row_dict["amount"] = float(row_dict["transaction_amount"])
        if "log_transaction_amount" not in row_dict and "transaction_amount" in row_dict:
            import numpy as np
            amt = float(row_dict["transaction_amount"])
            row_dict["log_transaction_amount"] = float(np.log1p(amt)) if amt > 0 else 0.0

        txn_id = str(row_dict.get("transaction_id", "TX_UNKNOWN"))

        # 1. Rule Engine Evaluation
        rule_eval = self.rule_engine.evaluate_transaction(row_dict)
        rule_score = float(rule_eval.rule_score)

        # 2. Supervised ML Score
        ml_score = 0.0
        df_single = pd.DataFrame([row_dict])
        for col in AML_FEATURE_COLUMNS:
            if col not in df_single.columns:
                df_single[col] = 0.0

        if self.supervised_model is not None:
            try:
                ml_score = float(self.supervised_model.predict_risk_score(df_single)[0])
            except Exception as e:
                logger.warning("Error running supervised ML scoring: %s", e)
                ml_score = rule_score

        # 3. Unsupervised Anomaly Score
        anom_score = 0.0
        if self.anomaly_model is not None:
            try:
                anom_score = float(self.anomaly_model.predict_anomaly_score(df_single)[0])
            except Exception as e:
                logger.warning("Error running anomaly detection: %s", e)
                anom_score = rule_score

        # 4. Network Score
        net_score = float(np.clip(network_score, 0.0, 100.0))

        # 5. Composite Risk Calculation
        final_risk = (
            (self.w_ml * ml_score) +
            (self.w_anom * anom_score) +
            (self.w_rule * rule_score) +
            (self.w_net * net_score)
        )
        final_risk = float(np.clip(final_risk, 0.0, 100.0))
        risk_level = settings.get_risk_level(final_risk)

        # 6. Feature Attributions (SHAP Explanations)
        attributions = []
        if include_attributions and self.explainer is not None:
            try:
                attr_list = self.explainer.explain_transaction(df_single.iloc[0], top_n=5)
                attributions = [a.to_dict() for a in attr_list]
            except Exception as e:
                logger.warning("Error generating SHAP attributions: %s", e)

        # 7. Explanatory Summary
        top_driver_str = ""
        if attributions:
            top_drivers = [f"{a['feature']} ({a['impact']})" for a in attributions[:2]]
            top_driver_str = f" Key ML drivers: {', '.join(top_drivers)}."

        summary = (
            f"Composite Risk Score: {final_risk:.1f}/100 [{risk_level}]. "
            f"Breakdown: ML={ml_score:.0f}, Anomaly={anom_score:.0f}, Rules={rule_score:.0f}, Network={net_score:.0f}. "
            f"{rule_eval.summary_explanation}{top_driver_str}"
        )

        return UnifiedRiskReport(
            transaction_id=txn_id,
            final_risk_score=final_risk,
            risk_level=risk_level,
            ml_score=ml_score,
            anomaly_score=anom_score,
            rule_score=rule_score,
            network_score=net_score,
            weights_used={
                "ml": round(self.w_ml, 2),
                "anomaly": round(self.w_anom, 2),
                "rules": round(self.w_rule, 2),
                "network": round(self.w_net, 2),
            },
            triggered_rules=[r.to_dict() for r in rule_eval.triggered_rules],
            feature_attributions=attributions,
            explanation_summary=summary,
        )


# Global singleton instance for API dependency injection
_unified_engine_instance: Optional[UnifiedRiskScoringEngine] = None


def get_risk_engine() -> UnifiedRiskScoringEngine:
    """Returns singleton instance of the Unified Risk Scoring Engine."""
    global _unified_engine_instance
    if _unified_engine_instance is None:
        _unified_engine_instance = UnifiedRiskScoringEngine()
    return _unified_engine_instance


def evaluate_transaction_risk(
    transaction_data: Dict[str, Any],
    network_score: float = 0.0,
    include_attributions: bool = True
) -> UnifiedRiskReport:
    """Evaluates composite risk score and SHAP attributions for a single transaction."""
    engine = get_risk_engine()
    return engine.calculate_risk(
        transaction_data,
        network_score=network_score,
        include_attributions=include_attributions
    )


def get_rule_engine() -> AMLRuleEngine:
    """Returns the rule engine instance."""
    return get_risk_engine().rule_engine


def evaluate_transaction_rules(transaction_data: Dict[str, Any]) -> RuleEvaluation:
    """Evaluates rule-based indicators for a transaction."""
    return get_rule_engine().evaluate_transaction(transaction_data)
