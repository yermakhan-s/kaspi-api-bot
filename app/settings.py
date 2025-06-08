from pydantic import BaseSettings

class Settings(BaseSettings):
    KASPI_TOKEN: str
    SHEET_ID: str              # ID таблицы из URL
    GOOGLE_CREDS_FILE: str = "creds.json"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    POLL_INTERVAL_MIN: int = 5  # интервал опроса Kaspi (мин.)

    class Config:
        env_file = ".env"

settings = Settings()

# Статусы Kaspi
ACTIVE_STATUSES = {"NEW", "SIGN_REQUIRED", "PICKUP", "DELIVERY", "KASPI_DELIVERY"}
FINAL_STATUSES  = {"COMPLETED", "CANCELLED", "RETURNED"}