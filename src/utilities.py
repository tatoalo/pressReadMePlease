import os
import sys
from pathlib import Path

from tomlkit import load

from configuration import Configuration
from notify import Notifier
from screenshot import Screenshot
from src import logging

EXAMPLE_CONFIG = "config_example.toml"


def load_configuration(*, path: Path = "config.toml") -> Configuration:
    if not os.path.exists(path):
        logging.debug(f"Configuration file not found in path `{path}`")
        if not os.path.exists(EXAMPLE_CONFIG):
            logging.debug(f"Couldn't even find the example config at `{path}`")
            sys.exit(1)
        path = EXAMPLE_CONFIG

    with open(path, "rb") as f:
        data = load(f)

    mlol = data.get("mlol")
    pressreader = data.get("pressreader")
    notification_service = data.get("notification_service", {})

    c = Configuration(
        mlol_website=mlol.get("website"),
        mlol_username=mlol.get("username"),
        mlol_password=mlol.get("password"),
        pressreader_username=pressreader.get("username"),
        pressreader_password=pressreader.get("password"),
        telegram_base_url=notification_service.get("telegram_base_url"),
        telegram_token=notification_service.get("telegram_token"),
        telegram_chat_id=notification_service.get("telegram_chat_id"),
    )

    return c


def load_notifier(*, configuration: Configuration, project_root: Path) -> Notifier:
    telegram_base_url = configuration.telegram_base_url
    telegram_token = configuration.telegram_token
    telegram_chat_id = configuration.telegram_chat_id

    notifier_instance = Notifier(
        url=telegram_base_url,
        token=telegram_token,
        chat_id=telegram_chat_id,
    )

    screenshot_instance = Screenshot(notifier=notifier_instance, path=project_root)

    notifier_instance.set_screenshot_client(screenshot_instance)

    return notifier_instance
