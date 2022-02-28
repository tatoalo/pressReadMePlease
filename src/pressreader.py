import sys

from playwright.sync_api import Browser, Page
from playwright.sync_api import TimeoutError

from notify import Notifier

NOTIFY = Notifier()


def visit_pressreader(b: Browser, page: Page, pressreader_auth: str = "", notification_service: Notifier = None):
    if notification_service is not None:
        global NOTIFY
        NOTIFY = notification_service

    print("Visiting Pressreader...")

    try:
        sign_in_button = page.query_selector(".btn-login")
        sign_in_button.click()

        login_pressreader(b, page, pressreader_auth)
        logout_pressreader(page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {visit_pressreader.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot('error')
            NOTIFY.screenshot_client.remove_screenshot()
        b.close()
        sys.exit(f"Element not found! {visit_pressreader.__name__} ; {e}")


def login_pressreader(b: Browser, page: Page, pressreader_auth: str):
    try:
        print("Logging into Pressreader...")
        username, password = pressreader_auth[0], pressreader_auth[1]

        page.fill("input[type='email']", username, timeout=0)
        page.fill("input[type='password']", password, timeout=0)

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = page.locator("label:has-text(\"Stay signed in\")")
        if stay_signed_in_checkbox.is_checked():
            stay_signed_in_checkbox.click()

        # Sign in procedure
        submit_button = page.query_selector(".btn-action >> text=Sign In")
        submit_button.click()
        # Checking whether credentials were wrong
        failed_login_procedure(b, page)

        select_publication_button(page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {login_pressreader.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot('error')
            NOTIFY.screenshot_client.remove_screenshot()
        b.close()
        sys.exit(f"Element not found! {login_pressreader.__name__} ; {e}")


def logout_pressreader(page: Page):
    try:
        profile_dialog_menu = page.query_selector('.userphoto-title')
        profile_dialog_menu.click()

        logout_item = page.query_selector('.pri-logout')
        logout_item.click()
    except TimeoutError:
        pass


def select_publication_button(page: Page):
    try:
        publication_button = page.query_selector("text=Select Publication")
        publication_button.click()
    except TimeoutError:
        pass


def failed_login_procedure(b: Browser, p: Page):
    try:
        wrong_credentials_warning = p.query_selector(".infomsg >> text=Invalid")
        if wrong_credentials_warning.is_visible():
            b.close()
            NOTIFY.send_message("Wrong Pressreader credentials!")
            sys.exit("Login failed, please check your Pressreader credentials!")
    except TimeoutError:
        pass
