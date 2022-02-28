import sys
import time

from notify import Notifier

from playwright.sync_api import Browser, Page
from playwright.sync_api import TimeoutError

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

        page.fill("input[type='email']", "lol@test.com", timeout=0)
        page.fill("input[type='password']", "lol", timeout=0)
        breakpoint()

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = page.locator("label:has-text(\"Stay signed in\")")
        if stay_signed_in_checkbox.is_checked():
            stay_signed_in_checkbox.click()

        # Sign in procedure
        submit_button = page.query_selector(".btn-action")

        with page.expect_response("**/services/auth/**") as response_info:
            submit_button.click()

        response = response_info.value
        print(f"{response.status}, {response.status_text}")

        # Checking whether credentials were wrong
        failed_login_procedure(b)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {login_pressreader.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot('error')
            NOTIFY.screenshot_client.remove_screenshot()
        b.close()
        sys.exit(f"Element not found! {login_pressreader.__name__} ; {e}")


def failed_login_procedure(b):
    try:
        time.sleep(2)
        wrong_credentials_warning = b.find_element_by_xpath("//div[@class='infomsg']/p").text
        if 'invalid' in wrong_credentials_warning.lower():
            b.close()
            NOTIFY.send_message("Wrong Pressreader credentials!")
            sys.exit("Login failed, please check your Pressreader credentials!")
    except NoSuchElementException:
        pass
