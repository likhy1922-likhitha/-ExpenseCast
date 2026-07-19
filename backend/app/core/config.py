"""
Central application configuration. All values are read from environment
variables (see backend/.env.example). Nothing here is hard-coded for a
specific deployment.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "ExpenseCast API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./expensecast.db"

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:5173"

    # --- ML model ---
    MODEL_PATH: str = "../machine-learning/models/lstm_expense_forecast.keras"
    SCALER_DIR: str = "../machine-learning/scalers"

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_TMP_DIR: str = "./tmp_uploads"

    # --- Demo mode ---
    ENABLE_DEMO_MODE: bool = True
    DEMO_USER_ID: str = "demo_user_001"

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
