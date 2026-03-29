import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    workspace_root: Path = Path("./workspace")
    openai_api_key: str = ""
    openai_url: str = "https://api.openai.com/v1"
    openai_model_name: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"


settings = Settings()
