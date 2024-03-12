"""Module for loading configuration settings."""

from __future__ import annotations

import yaml


def get_config() -> dict:
    """Loads configuration from the YAML file.

    Returns:
        dict: Configuration dictionary.
    """
    with open("config/config.yml", encoding="utf-8") as file:  # Specify encoding
        config = yaml.safe_load(file)
    return config
