from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CrediBot"
    app_env: str = "development"
    app_debug: bool = True
    app_public_url: str = ""

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""
    twilio_validate_signature: bool = False

    default_country_code: str = "593"


settings = Settings()
