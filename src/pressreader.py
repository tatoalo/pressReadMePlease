import sys
import time

from notify import Notifier

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

NOTIFY = Notifier()


def visit_pressreader(b, pressreader_auth="", notification_service=None):
    if notification_service is not None:
        global NOTIFY
        NOTIFY = notification_service

    # Switching to pressreader tab, target was `_blank' so I need
    # to iterate over the available handles, no biggie.
    # Being the target `_blank` the focus tab is immediately pressreader,
    # switch is required for changing page objects reference
    tabs = b.window_handles
    b.switch_to.window(tabs[1])
    print("Visiting Pressreader...")

    try:
        publications_button = WebDriverWait(b, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//label[@data-bind='click: selectTitle']/button[@type='submit']"))
        )

        b.execute_script("arguments[0].click();", publications_button)

        login_pressreader(b, pressreader_auth)

        # Waiting for 3 second before ceasing operations
        time.sleep(3)

    except TimeoutException:
        login_pressreader(b, pressreader_auth)
    except NoSuchElementException:
        try:
            time.sleep(2)
            publications_button = b.find_element_by_xpath(
                "//label[@data-bind='click: selectTitle']/button[@type='submit']")
            b.execute_script("arguments[0].click();", publications_button)
        except Exception as e:
            if not NOTIFY.disabled:
                NOTIFY.send_message(f"Error in {visit_pressreader.__name__} ; {e}")
                NOTIFY.screenshot_client.take_screenshot('error')
                NOTIFY.screenshot_client.remove_screenshot()
            b.quit()
            sys.exit(f"Element not found! {visit_pressreader.__name__} ; {e}")


def login_pressreader(b, pressreader_auth):
    try:
        print("Logging into Pressreader...")
        time.sleep(5)
        username, password = pressreader_auth[0], pressreader_auth[1]

        login_icon = locate_login_button(b)
        if login_icon:
            b.execute_script("arguments[0].click();", login_icon)
        else:
            b.quit()
            NOTIFY.send_message(f"Error in {login_pressreader.__name__} ; Login icon not found!")
            sys.exit(f"Element not found! {login_pressreader.__name__} ; Login icon not found!")

        time.sleep(2)
        pressreader_id = b.find_element_by_xpath("//input[@type='email']")
        pressreader_psw = b.find_element_by_xpath("//input[@type='password']")
        pressreader_id.send_keys(username)
        pressreader_psw.send_keys(password)

        # Unchecking `stay signed in checkbox`
        stay_signed_in_checkbox = b.find_element_by_xpath("//input[@type='checkbox']")
        b.execute_script("arguments[0].click();", stay_signed_in_checkbox)

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
        b.quit()
        sys.exit(f"Element not found! {login_pressreader.__name__} ; {e}")


# Moved logic to specific method in order to better handle the two existing cases found so far
def locate_login_button(b):
    login_icon = None

    try:
        login_icon = b.find_element_by_xpath("//button[@class='btn btn-login']")
    except NoSuchElementException:
        try:
            login_icon = b.find_element_by_xpath("//button[@class='btn btn-account']")
        except StaleElementReferenceException:
            # DOM has been refreshed, let's force find it in order not to lose
            # the reference pointer
            print("DOM has been refreshed, let's retry...")
            time.sleep(2)
            login_icon = b.find_element_by_xpath("//button[@class='btn btn-login']")

    return login_icon


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
