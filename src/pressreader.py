import sys
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def visit_pressreader(b, pressreader_auth=""):

    # Switching to pressreader tab, target was `_blank' so I need
    # to iterate over the available handles, no biggie.
    # Being the targe `_blank` the focus tab is immediately pressreader,
    # switch is required for changing page objects reference
    tabs = b.window_handles
    b.switch_to.window(tabs[1])
    print("Visiting Pressreader...")

    try:
        publications_button = WebDriverWait(b, 15).until(
            EC.presence_of_element_located((By.XPATH, "//label[@data-bind='click: selectTitle']/button[@type='submit']"))
        )

        publications_button.click()

        login_pressreader(b, pressreader_auth)

        # Waiting for 10 second before ceasing operations
        time.sleep(10)

    except NoSuchElementException:
        try:
            time.sleep(2)
            publications_button = b.find_element_by_xpath("//label[@data-bind='click: selectTitle']/button[@type='submit']")
            publications_button.click()
        except NoSuchElementException:
            b.close()
            sys.exit(f"Element not found! {visit_pressreader.__name__}")


def login_pressreader(b, pressreader_auth):
    try:
        print("Logging into Pressreader...")
        time.sleep(5)
        username, password = pressreader_auth[0], pressreader_auth[1]

        try:
            login_icon = b.find_element_by_xpath("//button[@aria-label='Log In']")
            login_icon.click()
        except StaleElementReferenceException or NoSuchElementException:
            # DOM has been refreshed, let's force find it in order not to lose
            # the reference pointer
            print("DOM has been refreshed, let's retry...")
            time.sleep(2)
            login_icon = b.find_element_by_xpath("//button[@aria-label='Log In']")
            login_icon.click()

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

    except NoSuchElementException:
        b.close()
        sys.exit(f"Element not found! {visit_pressreader.__name__}")