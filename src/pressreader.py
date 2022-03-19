import sys

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError

from chromium import Chromium
from notify import Notifier

NOTIFY = Notifier()
chromium = None


def visit_pressreader(page: Page, pressreader_auth: str = "", notification_service: Notifier = None):
    global chromium
    chromium = Chromium.get_chromium()
    if notification_service is not None:
        global NOTIFY
        NOTIFY = notification_service

    print("Visiting Pressreader...")

    try:
        publication_button = page.query_selector("xpath=//label[@data-bind='click: selectTitle']")
        if publication_button:
            publication_button.click()

        sign_in_button = page.locator(".btn-login")
        sign_in_button.wait_for()
        sign_in_button.click()

        login_pressreader(page, pressreader_auth)
        logout_pressreader(page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {visit_pressreader.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot(page, 'error')
            NOTIFY.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Element not found! {visit_pressreader.__name__} ; {e}")


def login_pressreader(page: Page, pressreader_auth: str):
    try:
        print("Logging into Pressreader...")
        username, password = pressreader_auth[0], pressreader_auth[1]

        page.fill("input[type='email']", username, timeout=0)
        page.fill("input[type='password']", password, timeout=0)

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = page.wait_for_selector('.checkbox')
        if stay_signed_in_checkbox.is_checked():
            stay_signed_in_checkbox.click()

        # Sign in procedure
        submit_button = page.wait_for_selector("xpath=//div[@class='pop-group']/a[@role='link']")
        submit_button.click()
        # Checking whether credentials were wrong
        failed_login_procedure(page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {login_pressreader.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot(page, 'error')
            NOTIFY.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Element not found! {login_pressreader.__name__} ; {e}")


def logout_pressreader(page: Page):
    try:
        profile_dialog_menu = page.wait_for_selector('.userphoto-title')
        profile_dialog_menu.click()

        logout_item = page.wait_for_selector('.pri-logout')
        logout_item.click()
    except TimeoutError:
        pass


def failed_login_procedure(p: Page):
    try:
        wrong_credentials_warning = p.query_selector(".infomsg >> text=Invalid")
        if wrong_credentials_warning and wrong_credentials_warning.is_visible():
            chromium.clean(debug_trace=True)
            NOTIFY.send_message("Wrong Pressreader credentials!")
            sys.exit("Login failed, please check your Pressreader credentials!")
    except TimeoutError:
        pass
