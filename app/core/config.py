from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    workspace_root: Path = Path("./workspace")
    active_template: str = "default"
    openai_api_key: str = ""
    openai_url: str = "https://api.openai.com/v1"
    openai_model_name: str = "gpt-4o-mini"

    @property
    def templates_root(self) -> Path:
        # 如果 active_template 是绝对路径或存在的路径，则直接使用
        template_path = Path(self.active_template)
        if template_path.is_absolute() and template_path.exists():
            return template_path
        
        # 否则，视为内置模板，在 app/assets/templates 下寻找
        builtin_path = Path(__file__).parent.parent / "assets" / "templates" / self.active_template
        return builtin_path

    @property
    def academy_root(self) -> Path:
        return self.workspace_root / "academy"

    @property
    def lineages_root(self) -> Path:
        return self.workspace_root / "lineages"

    @property
    def inner_root(self) -> Path:
        return self.workspace_root / "inner"

    @property
    def shrine_root(self) -> Path:
        return self.workspace_root / "shrine"

    class Config:
        env_file = ".env"


settings = Settings()
