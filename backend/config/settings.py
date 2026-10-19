from pathlib import Path
import os

from dotenv import load_dotenv
import yaml


PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]


def load_environment():
    load_dotenv(PROJECT_DIRECTORY / ".env", override=False)


def get_database_path():
    from storage.database import DEFAULT_DATABASE_PATH

    configured = os.getenv("DATABASE_PATH")
    if not configured:
        return DEFAULT_DATABASE_PATH
    path = Path(configured).expanduser()
    return path if path.is_absolute() else PROJECT_DIRECTORY / path


def get_config():
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config" / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config
