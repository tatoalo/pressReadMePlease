import sys

from notify import Notifier
from typing import List
from playwright.sync_api import Browser, Page
from playwright.sync_api import TimeoutError


NOTIFY = Notifier()


def visit_MLOL(b: Browser, page: Page, mlol_entrypoint: str = "", mlol_auth: List[str] = [], notification_service: Notifier = None):
    if notification_service is not None:
        global NOTIFY
        NOTIFY = notification_service

    print("Visiting MLOL...")
    page.goto(mlol_entrypoint, timeout=0)

    perform_login(b, page, mlol_auth)
    verify_error_modal_presence(page)
    new_page_tab = navigate_to_newspapers(b, page)

    breakpoint()
    return new_page_tab


def perform_login(b: Browser, page: Page, mlol_auth: List[str]):
    print("Logging into MLOL...")
    username, password = mlol_auth[0], mlol_auth[1]

    try:
        page.fill("input[name='lusername']", username, timeout=0)
        page.fill("input[name='lpassword']", password, timeout=0)

        page.click("input[type='submit']", timeout=0)

        # Checking failed login procedure
        failed_login_procedure(b, page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {perform_login.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot('error')
            NOTIFY.screenshot_client.remove_screenshot()
        b.close()
        sys.exit(f"Element not found! {perform_login.__name__} ; {e}")


def failed_login_procedure(b: Browser, page: Page):
    try:
        warning_failed_login = page.text_content(".page-title").lower()
        if 'avviso' in warning_failed_login:
            b.close()
            if not NOTIFY.disabled:
                NOTIFY.send_message("Wrong MLOL credentials!")
            sys.exit("Login failed, please check your MLOL credentials!")
    except TimeoutError:
        pass


def navigate_to_newspapers(b: Browser, page: Page):
    try:
        # Clicking on catalogue
        typologies_menu_entry = page.query_selector("#caricatip")
        typologies_menu_entry.click(timeout=0)

        newspapers_section = page.locator(":nth-match(:text('EDICOLA'), 1)")
        newspapers_section.click()

        # Focusing on Corriere della Sera, safe bet for a pressreader presence
        corriere_sera = page.locator("text=Corriere della Sera")
        corriere_sera.nth(0).click()

        pressreader_submit_button = page.locator(":nth-match(:text('SFOGLIA'), 1)")

        with page.expect_popup() as pressreader_blank_target:
            pressreader_submit_button.click()
        page_pressreader = pressreader_blank_target.value
        page_pressreader.wait_for_load_state("domcontentloaded")

        assert 'pressreader' in page_pressreader.title().lower(), Exception("Failed tab switch")

        return page_pressreader

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {navigate_to_newspapers.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot('error')
            NOTIFY.screenshot_client.remove_screenshot()
        b.close()
        sys.exit(f"Error in {navigate_to_newspapers.__name__} ; {e}")


def verify_error_modal_presence(page: Page):
    try:
        modal_outer_element = page.wait_for_selector(".modal-content", timeout=5)
        print("Modal found on MLOL entry")
        NOTIFY.send_message("Modal found in MLOL")
        NOTIFY.screenshot_client.take_screenshot('modal')
        NOTIFY.screenshot_client.remove_screenshot()

        # Retrieving modal dismissal button
        modal_dismissal_button = page.locator("//div[@class='modal-footer']/button[@data-dismiss='modal']")
        modal_dismissal_button.click()
        print("Modal dissmissed correctly!")

    except TimeoutError:
        # No modal found
        pass
