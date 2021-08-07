import sys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def visit_pressreader(b, pressreader_auth=""):

    WebDriverWait(b, 2)
    # Switching to pressreader tab, target was `_blank' so I need
    # to iterate over the available handles, no biggie.
    # Being the targe `_blank` the focus tab is immediately pressreader,
    # switch is required for changing page objects reference
    tabs = b.window_handles
    b.switch_to.window(tabs[1])

    try:
        WebDriverWait(b, 2)
        publications_button = b.find_element_by_xpath("//label[@data-bind='click: selectTitle']/button[@type='submit']")
        publications_button.click()
        # b.execute_script("arguments[0].click();", publications_button)
        login_pressreader(b, pressreader_auth)

        # Waiting for 1 second before logging out
        WebDriverWait(b, 1)
        logout_pressreader(b)

    except NoSuchElementException:
        print("HERE!")
        b.close()
        sys.exit(f"Element not found! {visit_pressreader.__name__}")


def login_pressreader(b, pressreader_auth):
    username, password = pressreader_auth[0], pressreader_auth[1]

    login_icon = WebDriverWait(b, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "userphoto"))
    )

    b.execute_script("arguments[0].click();", login_icon)

    pressreader_id = b.find_element_by_xpath("//input[@type='email']")
    pressreader_psw = b.find_element_by_xpath("//input[@type='password']")
    pressreader_id.send_keys(username)
    pressreader_psw.send_keys(password)

    # Unchecking `stay signed in checkbox`
    stay_signed_in_checkbox = b.find_element_by_xpath("//input[@type='checkbox']")
    b.execute_script("arguments[0].click();", stay_signed_in_checkbox)

    submit_button = b.find_element_by_xpath("//a[@role='link']")
    submit_button.click()


def logout_pressreader(b):
    return None