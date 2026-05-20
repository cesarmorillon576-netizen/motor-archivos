from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_USR: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()