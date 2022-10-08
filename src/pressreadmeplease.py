# from pathlib import Path

from playwright.sync_api import Page

from chromium import Chromium
from mlol import visit_MLOL
from pressreader import visit_pressreader
from src import CONFIGURATION, NOTIFIER, TIMEOUT


# PROJECT_ROOT = Path(__file__).parent
# env_path = Path(PROJECT_ROOT / "notification_service.env")

# TODO: re-enable this
# if env_path.is_file():
#     load_dotenv(dotenv_path=env_path)
#     TELEGRAM_BASE_URL = os.getenv("TELEGRAM_BASE_URL")
#     TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
#     TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

#     NOTIFY = Notifier(TELEGRAM_BASE_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
#     NOTIFY.screenshot_client = Screenshot(NOTIFY, path=PROJECT_ROOT)
# else:
# NOTIFY = Notifier()


def config_page(page: Page):
    window_size = {"width": 1920, "height": 1080}
    page.wait_for_load_state()
    page.set_viewport_size(viewport_size=window_size)
    page.set_default_timeout(TIMEOUT)


def main():
    mlol_link = CONFIGURATION.mlol_website
    mlol_credentials = (
        CONFIGURATION.mlol_username,
        CONFIGURATION.mlol_password,
    )
    pressreader_credentials = (
        CONFIGURATION.pressreader_username,
        CONFIGURATION.pressreader_password,
    )

    chromium = Chromium(headless=False, trace=True, timeout=TIMEOUT, notifier=NOTIFIER)
    chromium.context.on("page", config_page)
    chromium.context.new_page()
    pressreader_tab = visit_MLOL(mlol_entrypoint=mlol_link, mlol_auth=mlol_credentials)

    visit_pressreader(
        page=pressreader_tab,
        pressreader_auth=pressreader_credentials,
    )
    print("*** Automation flow has terminated correctly ***")
    chromium.clean()


if __name__ == "__main__":
    main()
