from tomlkit import load
from pathlib import Path
from configuration import Configuration
from notify import Notifier
from screenshot import Screenshot
import os
import sys


def load_configuration(*, path: Path = "config.toml") -> Configuration:
    if not os.path.exists(path):
        print(f"Configuration file not found in path `{path}`")
        sys.exit(1)

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

    n = Notifier(url=telegram_base_url, token=telegram_token, chat_id=telegram_chat_id)

    if None not in (telegram_base_url, telegram_token, telegram_chat_id):
        n.screenshot_client = Screenshot(n, path=project_root)

    return n
