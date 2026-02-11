import yaml
from src.models import AppConfig
def load_config(config_path: str = "config.yaml") -> AppConfig:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
