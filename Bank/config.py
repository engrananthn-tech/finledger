from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sqlalchemy_database_url: str
    BANK_WEBHOOK_SECRET : str
    model_config = {
        "env_file": ".env",
        "extra": "forbid"
    }

settings = Settings()
