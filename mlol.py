import sys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait


def visit_MLOL(b, mlol_entrypoint="", mlol_auth=[]):
    b.get(mlol_entrypoint)
    perform_login(b, mlol_auth)
    WebDriverWait(b, 2)
    navigate_to_newspapers(b)


def perform_login(b, mlol_auth):

    username, password = mlol_auth[0], mlol_auth[1]

    try:
        mlol_id = b.find_element_by_id("lusername")
        mlol_psw = b.find_element_by_id("lpassword")
        submit_button = b.find_element_by_xpath("//input[@type='submit']")

        mlol_id.send_keys(username)
        mlol_psw.send_keys(password)

        submit_button.submit()

    except NoSuchElementException:
        b.close()
        sys.exit(f"Element not found! {perform_login.__name__}")


def navigate_to_newspapers(b):
    try:
        # Clicking on catalogue
        typologies_menu_entry = b.find_element_by_xpath("//a[@id='caricatip']")
        typologies_menu_entry.click()

        newspapers_section = b.find_element_by_partial_link_text("EDICOLA")
        b.execute_script("arguments[0].click();", newspapers_section)

        # Focusing on Corriere della Sera, safe bet for a pressreader presence
        corriere_sera = b.find_element_by_partial_link_text("Sera")
        b.execute_script("arguments[0].click();", corriere_sera)

        pressreader_submit_button = b.find_element_by_partial_link_text("SFOGLIA")
        pressreader_submit_button.click()

    except NoSuchElementException:
        b.close()
        sys.exit(f"Element not found! {navigate_to_newspapers.__name__}")