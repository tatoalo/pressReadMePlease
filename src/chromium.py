import os
import sys
import weakref
from typing import Optional, Tuple

from playwright.sync_api import Page, Response, sync_playwright

# Native in 3.11 (https://peps.python.org/pep-0673/)
from typing_extensions import Self

from notify import Notifier
from src import PROJECT_ROOT, logging


class Chromium(object):
    _instance = []

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

    def __new__(
        cls,
        headless: bool = True,
        trace: bool = False,
        timeout: int = 0,
        notifier: Notifier = None,
    ) -> Self:
        if Chromium._instance:
            cls.__check_only_one_instance_alive()
            return weakref.proxy(Chromium._instance[0])
        else:
            instance_local = super().__new__(cls)
            Chromium._instance.append(instance_local)
            return instance_local

    def clean(self, debug_trace=False):
        if self.trace and debug_trace:
            self.__export_trace()
        logging.debug("Quitting Chromium...")
        if len(Chromium._instance) != 0:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            self._instance.remove(self)

    @staticmethod
    def get_chromium():
        if len(Chromium._instance) == 0:
            return Chromium()

        return Chromium._instance[0]

    def visit_site(self, page: Page, url: str) -> Optional[Response]:
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

        return response

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
            logging.debug(f"Found status {response.status} for {response.url}")
            return False, response.status
        return True, response.status

    def __check_only_one_instance_alive():
        if len(Chromium._instance) != 1:
            logging.error("Weird behaviour, too many alive references...exiting...")
            sys.exit("Weird behaviour, too many alive references...exiting...")
