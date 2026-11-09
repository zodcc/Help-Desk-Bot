from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Вычисляем абсолютный путь к корневой папке проекта
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Теперь указываем полный путь к файлу .env
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # Переменные из .env
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    OPERATOR_CHAT_ID: int | None = None

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/helpdesk.db"

    # Задел на будущее (веб-панель)
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8000
    JWT_SECRET: str = "change-me-in-production"
    ADMIN_PASSWORD: str = "Cecfyyf11"

    TZ: str = "Europe/Moscow"
    LOG_LEVEL: str = "INFO"

    # Удобное свойство: превращает строку "123,456" в список чисел [123, 456]
    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip()]

# Создаём глобальный объект настроек
settings = Settings()