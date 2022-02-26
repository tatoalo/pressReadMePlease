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

        page.fill("input[type='email']", "lol", timeout=0)
        page.fill("input[type='password']", "lol", timeout=0)
        breakpoint()

        # pressreader_id = b.find_element_by_xpath("//input[@type='email']")
        # pressreader_psw = b.find_element_by_xpath("//input[@type='password']")
        # pressreader_id.send_keys(username)
        # pressreader_psw.send_keys(password)

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = page.locator("label:has-text(\"Stay signed in\")")
        if not stay_signed_in_checkbox.is_checked():
            stay_signed_in_checkbox.click()

        # Sign in procedure
        submit_button = b.find_element_by_xpath("//div[@class='pop-group']/a[@role='link']")
        b.execute_script("arguments[0].click();", submit_button)

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
