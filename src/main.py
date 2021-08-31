from parse_credentials import extract_keys
from mlol import visit_MLOL
from pressreader import visit_pressreader
from notify import Notifier
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.chrome.options import Options


env_path = Path("/src/notification_service.env")
if env_path.is_file():
    load_dotenv(dotenv_path=env_path)
    TELEGRAM_BASE_URL = os.getenv('TELEGRAM_BASE_URL')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') 

    NOTIFY = Notifier(TELEGRAM_BASE_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
else:
    NOTIFY = Notifier()


def init_chrome():
    print("Launching Chrome...")

    opt_args = Options()
    opt_args.add_argument("--no-sandbox")
    opt_args.add_argument("--remote-debugging-port=9222")
    opt_args.add_argument("--headless")
    opt_args.add_argument("--disable-dev-shm-usage")
    opt_args.add_argument("--window-size=1920,1080")
    opt_args.add_argument("--disable-gpu")

    b = webdriver.Chrome(options=opt_args)

    return b


def close_browser(b):
    try:
        print("Terminating Chrome...")
        b.close()
    except NoSuchWindowException:
        sys.exit("Browser already closed.")


def main():

    # Retrieve credentials and MLOL entrypoint
    mlol_link, mlol_credentials, pressreader_credentials = extract_keys(path="/src/auth_data.txt")

    b = init_chrome()
    visit_MLOL(b, mlol_entrypoint=mlol_link, mlol_auth=mlol_credentials, notification_service=NOTIFY)
    visit_pressreader(b, pressreader_auth=pressreader_credentials, notification_service=NOTIFY)
    print("*** Automation flow has terminated correctly ***")
    close_browser(b)


if __name__ == "__main__":
    main()
