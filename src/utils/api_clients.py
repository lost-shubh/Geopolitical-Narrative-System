"""
Configuration and API helper utilities.
"""

import copy
import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_PIPELINE_CONFIG = {
    "topic": "geopolitics OR international conflict OR diplomacy",
    "days_back": 3,
    "max_articles": 20,
    "use_existing_data": True,
    "offline_mode": True,
    "max_social_comments": 250,
    "default_tone": "analytical",
}

DEFAULT_MODEL_CONFIG = {
    "sentiment_model": "distilbert-base-uncased-finetuned-sst-2-english",
    "emotion_model": "j-hartmann/emotion-english-distilroberta-base",
    "spacy_model": "en_core_web_sm",
    "prefer_transformers": False,
}

DEFAULT_API_KEYS_CONFIG = {
    "news_api_env": "NEWS_API_KEY",
    "news_api_key": "",
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def ensure_yaml_config(path: str | Path, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Load a YAML config file if present, otherwise return defaults."""
    config_path = Path(path)
    if not config_path.exists() or config_path.stat().st_size == 0:
        return copy.deepcopy(defaults)

    with open(config_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _deep_merge(defaults, data)


def load_pipeline_config(path: str | Path = "config/pipeline_config.yaml") -> Dict[str, Any]:
    return ensure_yaml_config(path, DEFAULT_PIPELINE_CONFIG)


def load_model_config(path: str | Path = "config/model_config.yaml") -> Dict[str, Any]:
    return ensure_yaml_config(path, DEFAULT_MODEL_CONFIG)


def load_api_config(path: str | Path = "config/api_keys.yaml") -> Dict[str, Any]:
    return ensure_yaml_config(path, DEFAULT_API_KEYS_CONFIG)


def get_news_api_key(api_config: Dict[str, Any] | None = None) -> str:
    """Resolve the news API key from env or yaml template."""
    api_config = api_config or load_api_config()
    env_name = api_config.get("news_api_env", "NEWS_API_KEY")
    return os.getenv(env_name, api_config.get("news_api_key", ""))
