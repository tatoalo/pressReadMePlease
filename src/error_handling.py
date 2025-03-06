import functools
import sys
from src import NOTIFIER, logging
from chromium import Chromium


def handle_errors(func):
    """Decorator to handle common error reporting and cleanup."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            page = args[0] if args else None

            NOTIFIER.send_message(f"Error in {func.__name__} ; {e}")

            if page is not None:
                NOTIFIER.screenshot_client.take_screenshot(page, "error")
                NOTIFIER.screenshot_client.remove_screenshot()
            else:
                logging.warning(
                    "Could not take screenshot: 'page' not found in arguments."
                )

            chromium = Chromium.get_chromium()
            chromium.clean(debug_trace=True)
            sys.exit(f"Workflow error! {func.__name__} ; {e}")

    return wrapper
