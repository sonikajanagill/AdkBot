from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    gemini_api_key: str = ""
    gcp_project_id: str = "adk-bot-sj-2026"
    gcp_location: str = "us-central1"
    agent_engine_id: str = "1051835704084004864"
    environment: Literal["dev", "prod"] = "dev"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @classmethod
    def load(cls) -> "Settings":
        """Loads config from local .env or from Google Secret Manager in prod."""
        settings = cls()
        
        if settings.environment == "prod":
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            
            def get_secret(secret_id: str) -> str:
                name = f"projects/{settings.gcp_project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")
                
            try:
                settings.telegram_bot_token = get_secret("TELEGRAM_BOT_TOKEN")
                settings.gemini_api_key = get_secret("GEMINI_API_KEY")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load secrets: {e}")
                
        return settings

settings = Settings.load()
