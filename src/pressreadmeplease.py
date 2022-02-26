import os

from mlol import visit_MLOL
from notify import Notifier
from screenshot import Screenshot
from parse_credentials import extract_keys
from pressreader import visit_pressreader

from dotenv import load_dotenv
from pathlib import Path
from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).parent
env_path = Path(PROJECT_ROOT / "notification_service.env")
if env_path.is_file():
    load_dotenv(dotenv_path=env_path)
    TELEGRAM_BASE_URL = os.getenv('TELEGRAM_BASE_URL')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    NOTIFY = Notifier(TELEGRAM_BASE_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    NOTIFY.screenshot_client = Screenshot(NOTIFY, path=PROJECT_ROOT)
else:
    NOTIFY = Notifier()


def init_chromium():
    print("Launching Chrome...")

    p = sync_playwright().start()
    b = p.chromium.launch(
        headless=False,
        slow_mo=5000,
        traces_dir=PROJECT_ROOT
    )
    page = b.new_page()
    page.set_viewport_size(viewport_size={
        "width": 1920,
        "height": 1080}
    )

    if NOTIFY.disabled is False:
        NOTIFY.screenshot_client.browser = b

    return b


def close_browser(b):
    print("Terminating Chrome...")
    b.close()


def main():
    # Retrieve credentials and MLOL entrypoint
    mlol_link, mlol_credentials, pressreader_credentials = extract_keys(path=PROJECT_ROOT / "auth_data.txt", notification_service=NOTIFY)

    b = init_chromium()
    visit_MLOL(b, mlol_entrypoint=mlol_link, mlol_auth=mlol_credentials, notification_service=NOTIFY)
    visit_pressreader(b, pressreader_auth=pressreader_credentials, notification_service=NOTIFY)
    print("*** Automation flow has terminated correctly ***")
    close_browser(b)


if __name__ == "__main__":
    main()
