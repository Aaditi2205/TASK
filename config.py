"""Application settings for Talk to Data."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Load configuration from environment variables and .env files."""

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	llm_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
	llm_model: str = Field(default="gemini-2.0-flash", validation_alias="LLM_MODEL")
	database_path: Path = Field(default=Path("data/Chinook.db"), validation_alias="DATABASE_PATH")
	max_rows: int = Field(default=100, validation_alias="MAX_ROWS")
	query_timeout: int = Field(default=30, validation_alias="QUERY_TIMEOUT")
	debug_mode: bool = Field(default=False, validation_alias="DEBUG_MODE")


settings = Settings()

