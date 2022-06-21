import os
from pathlib import Path

from playwright.sync_api import Page

from notify import Notifier


class Screenshot:
    def __init__(self, notifier: Notifier, path: Path):
        self.notifier = notifier
        self.path = path

        self.screenshot_path = None

    def take_screenshot(
        self, page: Page, filename: str = "screenshot", full_page: bool = False
    ):
        print(" ### Taking screenshot ###")
        self.screenshot_path = self.path / f"{filename}.png"

        page.screenshot(path=self.screenshot_path, full_page=full_page)
        self.notifier.send_image(image_location=self.screenshot_path)

    def remove_screenshot(self):
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
