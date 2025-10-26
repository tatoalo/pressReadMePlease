import os
import sys
from pathlib import Path

from playwright.sync_api import Page, TimeoutError

from chromium import Chromium
from error_handling import handle_errors
from src import NOTIFIER, PROJECT_ROOT, WARNING_FAILED_LOGIN_TEXT_ELEMENT, logging
from src import cache

chromium = None


def visit_MLOL(
    mlol_entrypoint: str = "",
    mlol_auth: tuple[str, str] = (None, None),
) -> Page:
    global chromium
    chromium = Chromium.get_chromium()

    logging.debug("Visiting MLOL...")
    page = chromium.context.pages[0]
    chromium.visit_site(page, mlol_entrypoint)

    perform_login(page, mlol_auth)
    verify_modal_presence(page)
    new_page_tab = navigate_to_newspapers(page)

    logout_mlol(page)

    return new_page_tab


@handle_errors
def perform_login(page: Page, mlol_auth: tuple[str, str]):
    logging.debug("Logging into MLOL...")
    username, password = mlol_auth

    page.fill("input[name='lusername']", username, timeout=0)
    page.fill("input[name='lpassword']", password, timeout=0)

    page.click("input[type='submit']", timeout=0)

    failed_login_procedure(page)


def failed_login_procedure(page: Page):
    try:
        warning_failed_login = page.text_content(".page-title").lower()
        if WARNING_FAILED_LOGIN_TEXT_ELEMENT in warning_failed_login:
            chromium.clean(debug_trace=True)
            NOTIFIER.send_message("Wrong MLOL credentials!")
            sys.exit("Login failed, please check your MLOL credentials!")
    except TimeoutError:
        pass


@handle_errors
def navigate_to_newspapers(page: Page) -> Page:
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


def verify_modal_presence(page: Page):
    try:
        page.wait_for_selector("#FavModal")
        logging.debug("Modal found on MLOL entry")

        # Caching check
        temp_screenshot_path = Path(PROJECT_ROOT) / "modal_temp.png"
        page.screenshot(path=temp_screenshot_path)

        # Check if we've seen this modal before
        if cache.should_notify_modal(temp_screenshot_path):
            logging.info("New modal detected - sending notification")
            NOTIFIER.send_message("Modal found in MLOL")
            NOTIFIER.send_image(image_location=temp_screenshot_path)
        else:
            logging.debug("Modal already seen - skipping notification")

        # Clean up temporary screenshot
        if temp_screenshot_path.exists():
            os.remove(temp_screenshot_path)

        # Retrieving modal dismissal button
        modal_dismissal_button = page.locator(
            "//div[@class='modal-footer']/button[@data-dismiss='modal']"
        )
        modal_dismissal_button.click()
        logging.debug("Modal dismissed correctly!")

    except TimeoutError:
        # No modal found
        pass


def logout_mlol(page: Page):
    try:
        logout_item = page.wait_for_selector(".btn-logout")
        logout_item.click()
    except TimeoutError:
        pass
