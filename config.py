import json
from typing import Any
from pydantic import BaseModel


class MirrorCopyConfig(BaseModel):
    from_path: str
    to_path: str

class Config(BaseModel):
    mirror_copy: MirrorCopyConfig


def load_config(config_path: str = "config.json") -> dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
        return {}