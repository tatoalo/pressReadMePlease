import os
from pathlib import Path
from typing import Type

from playwright.sync_api import Page

from src import logging


class Screenshot:
    def __init__(self, notifier: Type["Notifier"], path: Path):  # noqa: F821
        self.notifier = notifier
        self.path = path

        self.screenshot_path = None
        self.disabled = self.notifier.disabled

    def take_screenshot(
        self, page: Page, filename: str = "screenshot", full_page: bool = False
    ):
        if not self.disabled:
            logging.debug(" ### Taking screenshot ###")
            self.screenshot_path = self.path / f"{filename}.png"

            page.screenshot(path=self.screenshot_path, full_page=full_page)
            self.notifier.send_image(image_location=self.screenshot_path)

    def remove_screenshot(self):
        if not self.disabled:
            try:
                if self.screenshot_path:
                    os.remove(self.screenshot_path)
                else:
                    raise ScreenshotNotTaken(
                        "Screenshot has not been taken yet, thus cannot be removed!"
                    )
            except Exception:
                raise ScreenshotNotTaken(
                    "Screenshot has not been taken yet, thus cannot be removed!"
                )


class ScreenshotNotTaken(Exception):
    pass
