import os
import sys
from pathlib import Path
from datetime import datetime

from tomlkit import load, dump

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
        logfire_token=notification_service.get("logfire_token"),
        environment=notification_service.get("environment"),
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


def should_execute_flow() -> bool:
    from datetime import timedelta
    from src import CORRECT_FLOW_DAYS_RESET

    current_datetime = datetime.now()

    last_execution_result = _last_execution_time()

    if last_execution_result is None:
        logging.debug("*** No previous execution time found ***")
        return True

    last_execution_datetime, successful = last_execution_result

    logging.debug(
        "*** last execution time: {}, successful: {} ***".format(
            last_execution_datetime, successful
        )
    )

    if not successful:
        logging.debug("*** Last execution failed, running flow anyway ***")
        return True

    next_execution_time = last_execution_datetime + timedelta(
        days=CORRECT_FLOW_DAYS_RESET
    )
    return current_datetime >= next_execution_time


def _last_execution_time():
    from src import RUNNING_LOG_FILE

    path = Path(RUNNING_LOG_FILE)
    if path.exists():
        with path.open("r") as f:
            data = load(f)
            last_exec_str = data.get("last_execution_time", None)
            successful = data.get("successful", True)
            if last_exec_str:
                return datetime.fromisoformat(last_exec_str), successful
            return None
    else:
        with path.open("w") as f:
            data = {}
            dump(data, f)
        return None


def update_last_execution_time(successful: bool = True):
    from src import RUNNING_LOG_FILE

    path = Path(RUNNING_LOG_FILE)
    with path.open("w") as f:
        data = {
            "last_execution_time": datetime.now().isoformat(),
            "successful": successful,
        }
        dump(data, f)
