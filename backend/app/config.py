from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://dashboard:password@localhost:5432/agent_dashboard"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "agent-dashboard@example.com"
    ALERT_RECIPIENTS: str = ""
    RETENTION_DAYS: int = 30
    BASE_URL: str = "http://localhost"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
