from src.pressreadmeplease import init_chrome, close_browser, PROJECT_ROOT
from src.screenshot import Screenshot, ScreenshotNotTaken

import unittest
from pathlib import Path
from unittest import mock


class TestScreenshot(unittest.TestCase):

    @mock.patch('src.notify.Notifier')
    def setUp(self, mock_notifier) -> None:
        self.browser = init_chrome()
        self.screenshot = Screenshot(notifier=mock_notifier, path=PROJECT_ROOT, browser=self.browser)

    def tearDown(self) -> None:
        close_browser(self.browser)

    def test_screenshot_taken(self):
        self.screenshot.take_screenshot('tests/blank_screen')
        screenshot_file = Path(PROJECT_ROOT / "tests/blank_screen.png")

        self.assertTrue(screenshot_file.is_file(), "Screenshot has not been taken!")
        self.screenshot.remove_screenshot()

    def test_screenshot_not_taken_cannot_be_removed(self):
        with self.assertRaises(ScreenshotNotTaken):
            self.screenshot.remove_screenshot()


if __name__ == '__main__':
    unittest.main()