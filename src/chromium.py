import os
import sys
import weakref
from pathlib import Path
from typing import Tuple

from playwright.sync_api import Page, Response, sync_playwright

# Native in 3.11 (https://peps.python.org/pep-0673/)
from typing_extensions import Self

from notify import Notifier

PROJECT_ROOT = Path(__file__).parent
# chromium = None


# class Singleton(type):
#     _instances = WeakValueDictionary()

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             # This variable declaration is required to force a
#             # strong reference on the instance.
#             instance = super(Singleton, cls).__call__(*args, **kwargs)
#             cls._instances[cls] = instance
#         return cls._instances[cls]


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
            print("An istance was already running, using that instead")
            cls.__check_only_one_instance_alive()
            return weakref.proxy(Chromium._instance[0])
        else:
            instance_local = super().__new__(cls)
            Chromium._instance.append(instance_local)
            return instance_local

    def clean(self, debug_trace=False):
        if self.trace and debug_trace:
            self.__export_trace()
        print("Quitting Chromium...")
        if len(Chromium._instance) != 0:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            self._instance.remove(self)

    @staticmethod
    def get_chromium():
        # TODO: fix this method
        # global chromium

        if len(Chromium._instance) == 0:
            return Chromium()
        else:
            print("chromium is populated")

        return Chromium._instance[0]

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

    def __check_only_one_instance_alive():
        if len(Chromium._instance) != 1:
            sys.exit("Weird behaviour, too many alive references...exiting...")
