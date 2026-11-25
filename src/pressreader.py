import sys
from http import HTTPStatus
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Page, Response, TimeoutError

from chromium import Chromium
from error_handling import handle_errors
from src import EXPECTED_FREE_ACCESS_DAYS, NOTIFIER, logging

chromium = None

SIGNED_IN_SELECTOR = ".userphoto-title"
PUBLICATION_BUTTON_SELECTOR = "xpath=//label[@data-bind='click: selectTitle']"
SIGN_IN_PATH_SUFFIX = "/signin"

UNCONFIRMED_ACCESS_MESSAGE = (
    "PressReader access could not be confirmed: "
    "signed in, but no countdown or sponsor banner found"
)

LOGIN_OUTCOME_TIMEOUT = 15000
ACCESS_COUNTDOWN_TIMEOUT = 5000
HOTSPOT_DIALOG_TIMEOUT = 2000
LOGOUT_TIMEOUT = 5000


@handle_errors
def visit_pressreader(page: Page, pressreader_auth: tuple[str, str]) -> None:
    global chromium
    chromium = Chromium.get_chromium()

    logging.debug("Visiting Pressreader...")

    handle_cookie_consent(page)
    handle_publication_button(page)

    sign_in_button = page.get_by_role("button", name="Sign in")
    sign_in_button.click()

    login_pressreader(page, pressreader_auth)

    flow_executed_correctly, days, error_msg = verify_execution_flow(page)

    if not flow_executed_correctly:
        NOTIFIER.send_message(
            f"Flow was ***NOT** terminated correctly {visit_pressreader.__name__} ; {error_msg} ; days: {days}"
        )
        NOTIFIER.screenshot_client.take_screenshot(page, "error")
        NOTIFIER.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(
            f"Flow error {visit_pressreader.__name__} ; {error_msg} ; days: {days}"
        )

    logout_pressreader(page)


@handle_errors
def login_pressreader(p: Page, pressreader_auth: tuple[str, str]):
    logging.debug("Logging into Pressreader...")
    username, password = pressreader_auth

    p.fill("input[type='email']", username)
    p.fill("input[type='password']", password)

    stay_signed_in_checkbox = p.wait_for_selector(".checkbox")
    if stay_signed_in_checkbox.is_checked():
        stay_signed_in_checkbox.click()

    submit_button = p.wait_for_selector(
        "xpath=//div[@class='pop-group']/a[@role='link']"
    )
    sign_in_statuses = subscribe_to_login_event(p)
    submit_button.click()

    wait_for_login_outcome(p, sign_in_statuses)


def handle_publication_button(p: Page, timeout: Optional[int] = None):
    try:
        p.locator(PUBLICATION_BUTTON_SELECTOR).first.click(timeout=timeout)
    except TimeoutError:
        pass


def handle_cookie_consent(p: Page):
    try:
        deny_button = p.get_by_role("button", name="Deny")
        deny_button.click(timeout=5000)
        logging.debug("Cookie consent dismissed")
    except TimeoutError:
        pass


def verify_execution_flow(p: Page) -> tuple[bool, Optional[int], Optional[str]]:
    days = None
    try:
        free_access_time_element = p.locator("span[data-bind='text: freeAccessTime']")
        free_access_time_text = free_access_time_element.inner_text(
            timeout=ACCESS_COUNTDOWN_TIMEOUT
        )
    except TimeoutError:
        logging.debug(
            "freeAccessTime element not found, checking for sponsored access..."
        )
        if _is_sponsored_access_granted(p):
            return True, EXPECTED_FREE_ACCESS_DAYS, None
        if _is_authenticated_session(p):
            _report_unconfirmed_access(p)
            return True, EXPECTED_FREE_ACCESS_DAYS, None
        return False, days, "Error: Could not find free access time element!"

    if not free_access_time_text:
        return False, days, "Error: Free access time element is empty!"

    logging.info("PressReader access countdown: %s", free_access_time_text)

    days_validation_list = [
        int(n) for n in free_access_time_text.split("day")[0] if n.isdigit()
    ]

    if len(days_validation_list) == 0:
        return False, days, "Error: Could not extract days from free access time!"

    days = int("".join(map(str, days_validation_list)))

    return days == EXPECTED_FREE_ACCESS_DAYS, days, None


def _is_sponsored_access_granted(p: Page) -> bool:
    try:
        sponsored_element = p.get_by_text("brought to you by", exact=False)
        sponsored_element.wait_for(state="visible", timeout=5000)
        logging.debug("Sponsored access detected — flow considered successful")
        return True
    except TimeoutError:
        return False


def _is_authenticated_session(p: Page) -> bool:
    try:
        user_avatar = p.locator(SIGNED_IN_SELECTOR).first
        user_avatar.wait_for(state="visible", timeout=5000)
        return True
    except TimeoutError:
        return False


def _report_unconfirmed_access(p: Page) -> None:
    logging.warning(UNCONFIRMED_ACCESS_MESSAGE)
    NOTIFIER.send_message(UNCONFIRMED_ACCESS_MESSAGE)
    NOTIFIER.screenshot_client.take_screenshot(p, "unconfirmed_access")
    NOTIFIER.screenshot_client.remove_screenshot()


def logout_pressreader(p: Page):
    handle_publication_button(p, timeout=HOTSPOT_DIALOG_TIMEOUT)

    try:
        profile_dialog_menu = p.locator(SIGNED_IN_SELECTOR).first
        profile_dialog_menu.click(timeout=LOGOUT_TIMEOUT)

        logout_item = p.locator(".pri-logout").first
        logout_item.click(timeout=LOGOUT_TIMEOUT)
    except TimeoutError:
        logging.debug("PressReader logout did not complete")


def wait_for_login_outcome(p: Page, sign_in_statuses: list[int]):
    signed_in = p.locator(SIGNED_IN_SELECTOR).first
    wrong_credentials_warning = p.locator(".infomsg", has_text="Invalid").first

    try:
        signed_in.or_(wrong_credentials_warning).first.wait_for(
            state="visible", timeout=LOGIN_OUTCOME_TIMEOUT
        )
        sign_in_completed = True
    except TimeoutError:
        sign_in_completed = False

    access_denied = HTTPStatus.FORBIDDEN in sign_in_statuses

    if signed_in.is_visible():
        if access_denied:
            logging.warning(
                "PressReader sign-in returned 403 but the user is signed in"
            )
        return

    if access_denied:
        NOTIFIER.send_message("Access denied to PressReader: sign-in returned 403")
        chromium.clean(debug_trace=True)
        sys.exit("Access denied to PressReader!")

    if not sign_in_completed:
        raise Exception(
            "PressReader sign-in did not complete within "
            f"{LOGIN_OUTCOME_TIMEOUT // 1000}s"
        )

    if wrong_credentials_warning.is_visible():
        chromium.clean(debug_trace=True)
        NOTIFIER.send_message("Wrong Pressreader credentials!")
        sys.exit("Login failed, please check your Pressreader credentials!")


def is_sign_in_response(r: Response) -> bool:
    return urlparse(r.url).path.lower().endswith(SIGN_IN_PATH_SUFFIX)


def record_sign_in_response(r: Response, sign_in_statuses: list[int]) -> None:
    if is_sign_in_response(r):
        logging.debug(
            "PressReader sign-in response %s from %s", r.status, urlparse(r.url).path
        )
        sign_in_statuses.append(r.status)


def subscribe_to_login_event(p: Page) -> list[int]:
    sign_in_statuses = []
    p.on("response", lambda r: record_sign_in_response(r, sign_in_statuses))
    return sign_in_statuses
