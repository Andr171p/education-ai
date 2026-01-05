from typing import Final

from pathlib import Path

import pytz
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

TIMEZONE = pytz.timezone("Europe/Moscow")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
MEDIA_DIR = PROJECT_ROOT / ".media"
MEDIA_DIR.mkdir(exist_ok=True)
QDRANT_PATH = PROJECT_ROOT / ".tmp" / "langchain_qdrant"
QDRANT_PATH.mkdir(parents=True, exist_ok=True)
BASE_DIR = PROJECT_ROOT.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_")

    token: str = "<TOKEN>"


class NgrokSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NGROK_")

    url: str = "http://localhost:8000"


class SQLiteSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_")

    path: Path = BASE_DIR / "telegram-bot" / "db.sqlite3"
    driver: str = "aiosqlite"

    @property
    def sqlalchemy_url(self) -> str:
        return f"sqlite+{self.driver}:///{self.path}"


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    apikey: str = "<APIKEY>"


class YandexCloudSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YANDEX_CLOUD_")

    folder_id: str = "<FOLDER_ID>"
    apikey: str = "<APIKEY>"
    base_url: str = "https://llm.api.cloud.yandex.net/v1"

    @property
    def gemma_3_27b_it(self) -> str:
        return f"gpt://{self.folder_id}/gemma-3-27b-it/latest"

    @property
    def aliceai_llm(self) -> str:
        return f"gpt://{self.folder_id}/aliceai-llm"

    @property
    def qwen3_235b(self) -> str:
        return f"gpt://{self.folder_id}/qwen3-235b-a22b-fp8/latest"


class RAGSettings(BaseSettings):
    chunk_size: int = 1000
    chunk_overlap: int = 50


class Settings(BaseSettings):
    bot: BotSettings = BotSettings()
    ngrok: NgrokSettings = NgrokSettings()
    sqlite: SQLiteSettings = SQLiteSettings()
    openai: OpenAISettings = OpenAISettings()
    yandexcloud: YandexCloudSettings = YandexCloudSettings()
    rag: RAGSettings = RAGSettings()


settings: Final[Settings] = Settings()
