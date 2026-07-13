"""Configuración central de la aplicación usando variables de entorno."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lee y expone las variables de entorno definidas en el archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Configuración general de la aplicación ---
    app_name: str = "CrediBot"
    app_env: str = "development"
    app_debug: bool = True
    app_public_url: str = ""

    # --- Credenciales de Supabase (base de datos) ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # --- OpenAI (IA conversacional + RAG) ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_enable_ai: bool = True

    # --- Credenciales de Twilio (WhatsApp) ---
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""
    twilio_validate_signature: bool = False

    # --- Configuración regional ---
    default_country_code: str = "593"


settings = Settings()
