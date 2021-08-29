import sys
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def visit_MLOL(b, mlol_entrypoint="", mlol_auth=[]):
    print("Visiting MLOL...")
    b.get(mlol_entrypoint)
    perform_login(b, mlol_auth)
    time.sleep(2)
    verify_error_modal_presence(b)
    time.sleep(1)
    navigate_to_newspapers(b)


def perform_login(b, mlol_auth):
    print("Logging into MLOL...")
    username, password = mlol_auth[0], mlol_auth[1]

    try:
        mlol_id = b.find_element_by_id("lusername")
        mlol_psw = b.find_element_by_id("lpassword")
        submit_button = b.find_element_by_xpath("//input[@type='submit']")

        mlol_id.send_keys(username)
        mlol_psw.send_keys(password)

        submit_button.submit()

        time.sleep(2)
        # Checking failed login procedure
        failed_login_procedure(b)

    except NoSuchElementException:
        b.close()
        sys.exit(f"Element not found! {perform_login.__name__}")


def failed_login_procedure(b):

    try:
        warning_failed_login = b.find_element_by_xpath("//h1[@class='page-title']").text
        if 'avviso' in warning_failed_login.lower():
            sys.exit("Login failed, please check your MLOL credentials!")
    except NoSuchElementException:
        print("Login performed correctly")
        pass


def navigate_to_newspapers(b):
    try:
        # Clicking on catalogue
        typologies_menu_entry = b.find_element_by_xpath("//a[@id='caricatip']")
        typologies_menu_entry.click()

        newspapers_section = WebDriverWait(b, 15).until(
            EC.presence_of_element_located(
                (By.PARTIAL_LINK_TEXT, "EDICOLA"))
        )
        # newspapers_section = b.find_element_by_partial_link_text("EDICOLA")
        b.execute_script("arguments[0].click();", newspapers_section)

        # Focusing on Corriere della Sera, safe bet for a pressreader presence
        corriere_sera = b.find_element_by_partial_link_text("Sera")
        b.execute_script("arguments[0].click();", corriere_sera)

        pressreader_submit_button = b.find_element_by_partial_link_text("SFOGLIA")
        pressreader_submit_button.click()

    except Exception as e:
        b.close()
        sys.exit(f"Element not found! {navigate_to_newspapers.__name__}")


def verify_error_modal_presence(b):
    try:
        modal_outer_element = b.find_element_by_class_name("modal-content")
        print("Modal found on MLOL entry")

        # Retrieving modal dismissal button
        modal_dismiss_button = b.find_element_by_xpath("//div[@class='modal-footer']/button[@data-dismiss='modal']")
        modal_dismiss_button.click()
        print("Modal dissmissed correctly!")

    except NoSuchElementException:
        # No modal found
        pass
