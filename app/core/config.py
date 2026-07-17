from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017"
    apify_api_token: str | None = None
    redis_url: str | None = None
    cache_ttl_seconds: int = 300
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

_settings: Settings | None = None

def get_settings()->Settings:
    global _settings
    if _settings is None:
        _settings=Settings()
    return _settings
