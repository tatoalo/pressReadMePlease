import os
from pathlib import Path
from typing import Tuple

from playwright.sync_api import Page, Response, sync_playwright

from notify import Notifier

PROJECT_ROOT = Path(__file__).parent
chromium = None


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Chromium(metaclass=Singleton):
    def __init__(
        self,
        headless: bool = True,
        trace: bool = False,
        timeout: int = 0,
        notifier: Notifier = None,
    ):
        self.trace = trace
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context(locale="en-GB")
        self.context.clear_cookies()

        self.notifier = notifier
        self.timeout = timeout

        self.context.set_default_timeout(self.timeout)
        if self.trace:
            self.context.tracing.start(screenshots=True, snapshots=True)

    def clean(self, debug_trace=False):
        if self.trace and debug_trace:
            self.__export_trace()
        print("Quitting Chromium...")
        self.context.close()
        self.browser.close()

    @staticmethod
    def get_chromium():
        global chromium

        if chromium is None:
            chromium = Chromium()

        return chromium

    def visit_site(self, page: Page, url: str) -> None:
        response = page.goto(url)

        # If I get a status different from 200, I fail and communicate that
        response_check, status = self.__check_response_status(response)
        if not response_check:
            self.notifier.send_message(
                f"Error, {url} not reachable, got status {status}"
            )
            self.notifier.screenshot_client.take_screenshot(page, "error")
            self.notifier.screenshot_client.remove_screenshot()
            self.clean()

    def __export_trace(self) -> None:
        trace_path = PROJECT_ROOT / "debug_trace.zip"
        if self.notifier:
            self.context.tracing.stop(path=trace_path)
            self.notifier.send_binary(binary_path=trace_path)

        if trace_path:
            os.remove(trace_path)

    @staticmethod
    def __check_response_status(response: Response) -> Tuple[bool, int]:
        if response.status != 200:
            print(f"Found status {response.status} for {response.url}")
            return False, response.status
        return True, response.status
