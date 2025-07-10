import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))


class DBSettings(BaseSettings):
    name: str = Field("complaints.db", validation_alias='DB_NAME')

    @property
    def uri(self) -> str:
        # С поддержкой async
        return f'sqlite+aiosqlite:///{BASE_DIR}/{self.name}'

    @property
    def sync_uri(self) -> str:
        return f'sqlite:///{BASE_DIR}/{self.name}'

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class SentimentAPISettings(BaseSettings):
    api_key: str = Field(..., validation_alias='SENTIMENT_API_KEY')
    base_url: str = Field("https://api.apilayer.com/sentiment_analysis", validation_alias='SENTIMENT_API_URL')
    timeout: int = Field(10, validation_alias='SENTIMENT_API_TIMEOUT')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class OpenAISettings(BaseSettings):
    api_key: str = Field(..., validation_alias='OPENAI_API_KEY')
    model: str = Field("gpt-3.5-turbo", validation_alias='OPENAI_MODEL')
    max_tokens: int = Field(50, validation_alias='OPENAI_MAX_TOKENS')
    temperature: float = Field(0.1, validation_alias='OPENAI_TEMPERATURE')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class TelegramSettings(BaseSettings):
    bot_token: str = Field(..., validation_alias='TELEGRAM_BOT_TOKEN', description="Токен бота")
    chat_id: str = Field(..., validation_alias='TELEGRAM_CHAT_ID', description="ID чата/группы для уведомлений")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class GoogleSheetsSettings(BaseSettings):
    credentials_path: str = Field(..., validation_alias='GOOGLE_CREDENTIALS_PATH')
    spreadsheet_id: str = Field(..., validation_alias='GOOGLE_SPREADSHEET_ID')
    sheet_name: str = Field("Жалобы по оплате", validation_alias='GOOGLE_SHEET_NAME')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class OptionalAPISettings(BaseSettings):
    # Опциональные API для дополнительных фич
    spam_api_key: str = Field("", validation_alias='SPAM_API_KEY')
    spam_api_url: str = Field("https://api.apilayer.com/spamchecker?threshold=3", validation_alias='SPAM_API_URL')

    ip_api_url: str = Field("http://ip-api.com/json", validation_alias='IP_API_URL')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class AppSettings(BaseSettings):
    app_name: str = Field("Complaints Processing API", validation_alias='APP_NAME')
    debug: bool = Field(False, validation_alias='DEBUG')
    host: str = Field("0.0.0.0", validation_alias='HOST')
    port: int = Field(8000, validation_alias='PORT')

    # Настройки для n8n интеграции
    api_base_url: str = Field("http://localhost:8000", validation_alias='API_BASE_URL')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


class Settings(BaseSettings):
    db_settings: DBSettings = DBSettings()
    sentiment_api_settings: SentimentAPISettings = SentimentAPISettings()
    openai_settings: OpenAISettings = OpenAISettings()
    telegram_settings: TelegramSettings = TelegramSettings()
    google_sheets_settings: GoogleSheetsSettings = GoogleSheetsSettings()
    optional_api_settings: OptionalAPISettings = OptionalAPISettings()
    app_settings: AppSettings = AppSettings()

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


settings = Settings(_env_file=f"{BASE_DIR}/.env", _env_file_encoding='utf-8')