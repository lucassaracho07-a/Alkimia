import os

from dotenv import load_dotenv

from app.paths import app_data_dir, app_root, is_frozen, resource_path
from app.version import APP_VERSION

BASE_DIR = app_root()


def _load_env() -> None:
    if is_frozen():
        candidates = [
            app_data_dir() / ".env",
            app_root() / ".env",
            resource_path(".env"),
        ]
    else:
        candidates = [
            app_root() / ".env",
            app_data_dir() / ".env",
        ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path)
            return


_load_env()


class Settings:
    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self.app_title = os.getenv("APP_TITLE", "ALKIMIA POS").strip()
        self.app_version = APP_VERSION

    def validate(self) -> None:
        missing = []
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")
        if missing:
            raise RuntimeError(
                "Faltan variables en el archivo .env: " + ", ".join(missing)
            )


settings = Settings()
