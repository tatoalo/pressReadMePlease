from pathlib import Path
from sys import exit, platform
from unittest import TestCase, mock

from src.chromium import Chromium
from src.screenshot import Screenshot

# Testing the virtual display only in the Ubuntu Docker container
if platform == "darwin":
    HEADLESS = True
    VIRTUAL_DISPLAY = False
elif platform == "linux":
    from pyvirtualdisplay import Display

    HEADLESS = False
    VIRTUAL_DISPLAY = True
else:
    exit("GTFO!")

TEST_PATH = Path(__file__).parent


class TestCloudflare(TestCase):
    @mock.patch("src.notify.Notifier")
    def setUp(self, notifier_mock) -> None:

        if VIRTUAL_DISPLAY:
            self.d = Display()
            self.d.start()

        self.chromium = Chromium(headless=HEADLESS)
        self.chromium.context.new_page()
        self.page = self.chromium.context.pages[0]

        self.screenshot = Screenshot(notifier=notifier_mock, path=TEST_PATH)

    def tearDown(self) -> None:
        if VIRTUAL_DISPLAY:
            self.d.stop()

    def test_user_agent_is_valid(self):
        self.page.goto("https://bot.sannysoft.com/")
        self.screenshot.take_screenshot(
            self.page, f"fingerprint_report_{platform}", full_page=True
        )

        user_agent = self.page.locator("tr:has-text('PHANTOM_UA')").inner_text().lower()

        self.assertIn(
            "chrome",
            user_agent,
            "Not using Chrome, which should be weird at this point...",
        )

        if not HEADLESS:
            # Super lazy, but OK for the time being :D
            self.assertNotIn(
                "headless", user_agent, f"User agent is headless! - platform {platform}"
            )
        else:
            self.assertIn(
                "headless",
                user_agent,
                f"User agent is NOT headless! - platform {platform}",
            )
