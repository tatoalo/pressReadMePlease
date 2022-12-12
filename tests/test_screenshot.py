from pathlib import Path
from unittest import mock, TestCase

from src.chromium import Chromium

from src.screenshot import Screenshot, ScreenshotNotTaken


TEST_PATH = Path(__file__).parent


class TestScreenshot(TestCase):
    @mock.patch("src.notify.Notifier")
    def setUp(self, notifier_mock) -> None:
        notifier_mock.disabled = False

        self.chromium = Chromium()
        self.chromium.context.new_page()
        self.page = self.chromium.context.pages[0]

        self.screenshot = Screenshot(notifier=notifier_mock, path=TEST_PATH)

    def tearDown(self) -> None:
        self.chromium.clean()

    def test_screenshot_taken(self):
        self.screenshot.take_screenshot(self.page, "blank_screen")

        screenshot_file = Path(TEST_PATH / "blank_screen.png")

        self.assertTrue(screenshot_file.is_file(), "Screenshot has not been taken!")
        self.screenshot.remove_screenshot()

    def test_screenshot_not_taken_cannot_be_removed(self):
        with self.assertRaises(ScreenshotNotTaken):
            self.screenshot.remove_screenshot()
