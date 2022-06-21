import sys
from typing import List

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError

from chromium import Chromium
from notify import Notifier

NOTIFY = Notifier()
chromium = None


def visit_MLOL(
    mlol_entrypoint: str = "",
    mlol_auth: List[str] = [],
    notification_service: Notifier = None,
) -> Page:
    global chromium
    chromium = Chromium.get_chromium()
    if notification_service is not None:
        global NOTIFY
        NOTIFY = notification_service

    print("Visiting MLOL...")
    page = chromium.context.pages[0]
    chromium.visit_site(page, mlol_entrypoint)

    perform_login(page, mlol_auth)
    verify_modal_presence(page)
    new_page_tab = navigate_to_newspapers(page)

    logout_mlol(page)

    return new_page_tab


def perform_login(page: Page, mlol_auth: List[str]):
    print("Logging into MLOL...")
    username, password = mlol_auth[0], mlol_auth[1]

    try:
        page.fill("input[name='lusername']", username, timeout=0)
        page.fill("input[name='lpassword']", password, timeout=0)

        page.click("input[type='submit']", timeout=0)

        # Checking failed login procedure
        failed_login_procedure(page)

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {perform_login.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot(page, "error")
            NOTIFY.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Element not found! {perform_login.__name__} ; {e}")


def failed_login_procedure(page: Page):
    try:
        warning_failed_login = page.text_content(".page-title").lower()
        if "avviso" in warning_failed_login:
            chromium.clean(debug_trace=True)
            if not NOTIFY.disabled:
                NOTIFY.send_message("Wrong MLOL credentials!")
            sys.exit("Login failed, please check your MLOL credentials!")
    except TimeoutError:
        pass


def navigate_to_newspapers(page: Page) -> Page:
    try:
        # Clicking on catalogue
        typologies_menu_entry = page.query_selector("#caricatip")
        typologies_menu_entry.click()

        newspapers_section = page.locator(":nth-match(:text('EDICOLA'), 1)")
        newspapers_section.click()

        # Focusing on Corriere della Sera, safe bet for a pressreader presence
        corriere_sera = page.locator("text=Corriere della Sera")
        corriere_sera.nth(0).click()

        pressreader_submit_button = page.locator(":nth-match(:text('SFOGLIA'), 1)")

        with chromium.context.expect_page() as pressreader_blank_target:
            pressreader_submit_button.click()
        page_pressreader = pressreader_blank_target.value
        page_pressreader.wait_for_load_state("domcontentloaded")

        assert "pressreader" in page_pressreader.title().lower(), Exception(
            "Failed tab switch"
        )

        return page_pressreader

    except Exception as e:
        if not NOTIFY.disabled:
            NOTIFY.send_message(f"Error in {navigate_to_newspapers.__name__} ; {e}")
            NOTIFY.screenshot_client.take_screenshot(page, "error")
            NOTIFY.screenshot_client.remove_screenshot()
        chromium.clean(debug_trace=True)
        sys.exit(f"Error in {navigate_to_newspapers.__name__} ; {e}")


def verify_modal_presence(page: Page):
    try:
        page.wait_for_selector("#FavModal")
        print("Modal found on MLOL entry")
        if not NOTIFY.disabled:
            NOTIFY.send_message("Modal found in MLOL")
            NOTIFY.screenshot_client.take_screenshot(page, "modal")
            NOTIFY.screenshot_client.remove_screenshot()

        # Retrieving modal dismissal button
        modal_dismissal_button = page.locator(
            "//div[@class='modal-footer']/button[@data-dismiss='modal']"
        )
        modal_dismissal_button.click()
        print("Modal dissmissed correctly!")

    except TimeoutError:
        # No modal found
        pass


def logout_mlol(page: Page):
    try:
        logout_item = page.wait_for_selector(".btn-logout")
        logout_item.click()
    except TimeoutError:
        pass
