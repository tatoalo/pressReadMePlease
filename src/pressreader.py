import sys
from http import HTTPStatus
from typing import Tuple

from playwright.sync_api import Page, Response, TimeoutError

from chromium import Chromium
from src import NOTIFIER, CORRECT_FLOW_DAYS_RESET

chromium = None


def visit_pressreader(page: Page, pressreader_auth: Tuple[str, str]) -> None:
    global chromium
    chromium = Chromium.get_chromium()

    print("Visiting Pressreader...")

    try:
        handle_publication_button(page)

        sign_in_button = page.locator(".btn-login")
        sign_in_button.click()

        login_pressreader(page, pressreader_auth)

        hs_button = page.locator(".btn-hotspot")
        hs_button.click()

        flow_executed_correctly, error_msg = verify_execution_flow(page)

        if not flow_executed_correctly:
            NOTIFIER.send_message(
                f"Flow was ***NOT** terminated correctly {visit_pressreader.__name__} ; {error_msg}"
            )
            NOTIFIER.screenshot_client.take_screenshot(page, "error")
            NOTIFIER.screenshot_client.remove_screenshot()
            chromium.clean(debug_trace=True)
            sys.exit(f"Flow error {visit_pressreader.__name__} ; {error_msg}")

        logout_pressreader(page)

    except Exception as e:
        NOTIFIER.send_message(f"Error in {visit_pressreader.__name__} ; {e}")
        NOTIFIER.screenshot_client.take_screenshot(page, "error")
        NOTIFIER.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Element not found! {visit_pressreader.__name__} ; {e}")


def login_pressreader(p: Page, pressreader_auth: Tuple):
    try:
        print("Logging into Pressreader...")
        username, password = pressreader_auth

        p.fill("input[type='email']", username, timeout=0)
        p.fill("input[type='password']", password, timeout=0)

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = p.wait_for_selector(".checkbox")
        if stay_signed_in_checkbox.is_checked():
            stay_signed_in_checkbox.click()

        # Sign in procedure
        submit_button = p.wait_for_selector(
            "xpath=//div[@class='pop-group']/a[@role='link']"
        )
        submit_button.click()
        subscribe_to_login_event(p)

        # Checking whether credentials were wrong
        failed_login_procedure(p)

    except Exception as e:
        NOTIFIER.send_message(f"Error in {login_pressreader.__name__} ; {e}")
        NOTIFIER.screenshot_client.take_screenshot(p, "error")
        NOTIFIER.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Element not found! {login_pressreader.__name__} ; {e}")


def handle_publication_button(p: Page):
    try:
        publication_button = p.wait_for_selector(
            "xpath=//label[@data-bind='click: selectTitle']"
        )
        publication_button.click()

    except TimeoutError:
        pass


def verify_execution_flow(p: Page) -> Tuple:
    welcome_message = p.locator(".infomsg-optional")

    if not welcome_message:
        return False, "Error in welcome message filtering!"

    correct_flow_days_reset = 6

    days_validation_list = [
        int(n) for n in welcome_message.inner_text().split("day")[0] if n.isdigit()
    ]

    if len(days_validation_list) == 0:
        return False, "Error in validation extraction!"

    days = int("".join(map(str, days_validation_list)))

    return days == correct_flow_days_reset, None


def logout_pressreader(p: Page):
    try:
        profile_dialog_menu = p.wait_for_selector(".userphoto-title")
        profile_dialog_menu.click()

        logout_item = p.wait_for_selector(".pri-logout")
        logout_item.click()
    except TimeoutError:
        pass


def failed_login_procedure(p: Page):
    try:
        wrong_credentials_warning = p.query_selector(".infomsg >> text=Invalid")
        if wrong_credentials_warning and wrong_credentials_warning.is_visible():
            chromium.clean(debug_trace=True)
            NOTIFIER.send_message("Wrong Pressreader credentials!")
            sys.exit("Login failed, please check your Pressreader credentials!")
    except TimeoutError:
        pass


def handle_sign_in_event(r: Response) -> None:
    if r.status == HTTPStatus.FORBIDDEN:
        NOTIFIER.send_message(
            f"Access denied to PressReader website \
            {handle_sign_in_event.__name__}"
        )
        chromium.clean(debug_trace=True)
        sys.exit("Access denied to PressReader!")


def __filter_response_login_event(r: Response) -> bool:
    if "Authentication/SignIn" in r.url:
        handle_sign_in_event(r)
        return True

    return False


def subscribe_to_login_event(p: Page):
    p.on("response", lambda r: __filter_response_login_event(r))
