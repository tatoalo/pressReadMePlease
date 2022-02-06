import os


class Screenshot:
    def __init__(self, notifier, path, browser=None):
        self.notifier = notifier
        self.browser = browser
        self.path = path

        self.screenshot_path = None

    def take_screenshot(self, filename='screenshot'):
        print(" ### Taking screenshot ###")
        self.screenshot_path = self.path / f"{filename}.png"

        self.browser.save_screenshot(str(self.screenshot_path))
        self.notifier.send_image(self.screenshot_path)

    def remove_screenshot(self):
        if self.screenshot_path:
            os.remove(self.screenshot_path)
        else:
            raise ScreenshotNotTaken("Screenshot has not been taken yet, thus cannot be removed!")


class ScreenshotNotTaken(Exception):
    pass
