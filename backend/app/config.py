"""
Configuration module for the AML Investigation System.

Loads settings from environment variables (via .env file).
All configuration is centralized here — never hard-code secrets elsewhere.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Priority order:
      1. Actual environment variables
      2. .env file values
      3. Field default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = "AML Investigation System"
    app_version: str = "1.0.0"
    debug: bool = False
    random_seed: int = 42
    log_level: str = "INFO"

    # -------------------------------------------------------------------------
    # API
    # -------------------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./aml_local.db"

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_A_LONG_RANDOM_STRING"
    api_key_header: str = "X-API-Key"

    # -------------------------------------------------------------------------
    # Model / ML Paths
    # -------------------------------------------------------------------------
    model_dir: str = "./models/v1"
    fraud_classifier_path: str = "./models/v1/fraud_classifier.pkl"
    anomaly_detector_path: str = "./models/v1/anomaly_detector.pkl"
    feature_scaler_path: str = "./models/v1/feature_scaler.pkl"

    # -------------------------------------------------------------------------
    # Data Paths
    # -------------------------------------------------------------------------
    raw_data_dir: str = "./ml/data/raw"
    processed_data_dir: str = "./ml/data/processed"
    synthetic_data_dir: str = "./ml/data/synthetic"

    # -------------------------------------------------------------------------
    # Risk Engine Weights (must sum to 1.0)
    # -------------------------------------------------------------------------
    risk_weight_ml: float = 0.40
    risk_weight_anomaly: float = 0.20
    risk_weight_rules: float = 0.20
    risk_weight_network: float = 0.20

    @field_validator("risk_weight_ml", "risk_weight_anomaly", "risk_weight_rules", "risk_weight_network")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Risk weights must be between 0.0 and 1.0")
        return v

    # -------------------------------------------------------------------------
    # Risk Thresholds
    # -------------------------------------------------------------------------
    risk_low_max: int = 29
    risk_medium_max: int = 59
    risk_high_max: int = 79

    def get_risk_level(self, score: float) -> str:
        """
        Convert a numeric risk score (0–100) to a human-readable risk level.
        
        These are application UI thresholds — not legal determinations.
        """
        score = max(0.0, min(100.0, score))
        if score <= self.risk_low_max:
            return "LOW"
        elif score <= self.risk_medium_max:
            return "MEDIUM"
        elif score <= self.risk_high_max:
            return "HIGH"
        return "CRITICAL"

    @property
    def model_dir_path(self) -> Path:
        return Path(self.model_dir)

    @property
    def fraud_classifier_exists(self) -> bool:
        return Path(self.fraud_classifier_path).exists()

    @property
    def anomaly_detector_exists(self) -> bool:
        return Path(self.anomaly_detector_path).exists()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return cached application settings singleton.
    
    Using lru_cache ensures settings are loaded once and reused,
    avoiding repeated file I/O on every request.
    """
    return Settings()
