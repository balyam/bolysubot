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
    
    # App Settings
    DEBUG: bool = False
    PHOTOS_DIR: str = "storage/photos/contractors"
    
    # Access Control
    ACCESS_MODE: str = "open"  # open, whitelist, invite_only
    ADMIN_TELEGRAM_IDS: str = ""  # Comma-separated admin telegram IDs
    INVITE_TOKEN: str = ""  # Токен для первого входа (если ACCESS_MODE=invite_only)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
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


# Создаем глобальный экземпляр настроек
settings = Settings()

