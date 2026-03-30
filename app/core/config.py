import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    workspace_root: Path = Path("./workspace")
    templates_root: Path = Path(__file__).parent.parent / "assets" / "templates" / "default"
    openai_api_key: str = ""
    openai_url: str = "https://api.openai.com/v1"
    openai_model_name: str = "gpt-4o-mini"

    @property
    def academy_root(self) -> Path:
        return self.workspace_root / "academy"

    @property
    def lineages_root(self) -> Path:
        return self.workspace_root / "lineages"

    @property
    def lineage_root(self) -> Path:
        return self.workspace_root / "lineage"

    class Config:
        env_file = ".env"


settings = Settings()
