from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str
    
    # Database
    DATABASE_URL: str
    
    # Admin Panel
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_SECRET_KEY: str
    SESSION_HTTPS_ONLY: bool = False  # True в проде: cookie админки только по HTTPS
    
    # App Settings
    DEBUG: bool = False
    PHOTOS_DIR: str = "storage/photos/contractors"
    
    # Webhook Settings
    USE_WEBHOOK: bool = False  # False = polling, True = webhook
    WEBHOOK_HOST: str = ""  # Например: https://yourdomain.com
    WEBHOOK_PATH: str = "/webhook"  # Путь для webhook
    WEBHOOK_SECRET: str = ""  # Секретный токен для проверки webhook
    
    # Web App Settings
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8000
    
    # Access Control
    ACCESS_MODE: str = "open"  # open, whitelist, invite_only
    ADMIN_TELEGRAM_IDS: str = ""  # Comma-separated admin telegram IDs
    INVITE_TOKEN: str = ""  # Токен для первого входа (если ACCESS_MODE=invite_only)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @model_validator(mode="after")
    def _check_webhook(self) -> "Settings":
        if self.USE_WEBHOOK:
            if not self.WEBHOOK_HOST.startswith("https://"):
                raise ValueError("USE_WEBHOOK=True требует WEBHOOK_HOST вида https://домен")
            if not self.WEBHOOK_SECRET:
                raise ValueError("USE_WEBHOOK=True требует WEBHOOK_SECRET (иначе webhook примет запрос от кого угодно)")
        return self
    
    @property
    def photos_path(self) -> Path:
        """Возвращает Path объект для директории с фото"""
        path = Path(self.PHOTOS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def admin_ids(self) -> list[int]:
        """Список Telegram ID администраторов"""
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        return [int(id_.strip()) for id_ in self.ADMIN_TELEGRAM_IDS.split(",") if id_.strip()]
    
    @property
    def webhook_url(self) -> str:
        """Полный URL webhook"""
        if not self.WEBHOOK_HOST:
            return ""
        return f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"


# Создаем глобальный экземпляр настроек
settings = Settings()

