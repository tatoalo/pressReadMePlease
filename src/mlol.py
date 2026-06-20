import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, TimeoutError

from chromium import Chromium
from error_handling import handle_errors
from src import (
    NOTIFIER,
    PROJECT_ROOT,
    WARNING_FAILED_LOGIN_TEXT_ELEMENT,
    cache,
    logging,
)

chromium = None

MLOL_LOGIN_PATH = "/login/login"
MLOL_LOGIN_FORM_SELECTOR = "#Username"


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

    open_login_form(page)

    page.fill(MLOL_LOGIN_FORM_SELECTOR, username)
    page.fill("#Password", password)

    page.press("#Password", "Enter")
    page.wait_for_load_state("domcontentloaded")

    failed_login_procedure(page)


def open_login_form(page: Page) -> None:
    if login_form_is_available(page):
        return

    try:
        page.get_by_role("button", name="Accedi").first.click(timeout=5000)
        page.wait_for_selector(MLOL_LOGIN_FORM_SELECTOR, timeout=5000)
        return
    except TimeoutError:
        logging.debug("MLOL clean-page Accedi button unavailable, trying login URL")

    parsed_url = urlparse(page.url)
    mlol_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    page.goto(urljoin(mlol_base_url, MLOL_LOGIN_PATH))
    page.wait_for_load_state("domcontentloaded")


def login_form_is_available(page: Page) -> bool:
    try:
        page.wait_for_selector(MLOL_LOGIN_FORM_SELECTOR, timeout=1000)
        return True
    except TimeoutError:
        return False


def failed_login_procedure(page: Page):
    try:
        warning_failed_login = page.text_content(".page-title", timeout=5000).lower()
        if WARNING_FAILED_LOGIN_TEXT_ELEMENT in warning_failed_login:
            chromium.clean(debug_trace=True)
            NOTIFIER.send_message("Wrong MLOL credentials!")
            sys.exit("Login failed, please check your MLOL credentials!")
    except TimeoutError:
        pass


@handle_errors
def navigate_to_newspapers(page: Page) -> Page:
    parsed_url = urlparse(page.url)
    mlol_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    page.goto(urljoin(mlol_base_url, "/search?idtype=600"))
    page.wait_for_load_state("networkidle")

    corriere_href = page.eval_on_selector_all(
        "a[href*='/media/details/']",
        "els=>{for(const e of els){"
        "if((e.innerText||'').trim().toLowerCase()==='corriere della sera')"
        "return e.getAttribute('href');}return null;}",
    )
    if not corriere_href:
        raise Exception("Corriere della Sera not found in Edicola listing")

    page.goto(urljoin(mlol_base_url, corriere_href))
    page.wait_for_load_state("networkidle")

    dismiss_onboarding_modal(page)

    sfoglia_button = page.get_by_role("link", name="Sfoglia online").first

    with chromium.context.expect_page() as pressreader_blank_target:
        sfoglia_button.click()
    page_pressreader = pressreader_blank_target.value
    page_pressreader.wait_for_load_state("domcontentloaded")

    assert "pressreader" in page_pressreader.title().lower(), Exception(
        "Failed tab switch"
    )

    return page_pressreader


def dismiss_onboarding_modal(page: Page):
    container = "#modal-onboardingontainer"
    try:
        page.wait_for_selector(f"{container} .modal-body", timeout=3000)
    except TimeoutError:
        return

    logging.debug("Onboarding modal detected - dismissing")

    close_selectors = (
        f"{container} [data-dismiss='modal']",
        f"{container} [data-bs-dismiss='modal']",
        f"{container} .btn-close",
        f"{container} button.close",
    )
    for selector in close_selectors:
        try:
            page.locator(selector).first.click(timeout=2000)
            logging.debug(f"Onboarding modal dismissed via {selector}")
            break
        except TimeoutError:
            continue

    page.evaluate(
        "(sel)=>{"
        "const c=document.querySelector(sel);"
        "if(c){c.innerHTML='';c.remove();}"
        "document.querySelectorAll('.modal-backdrop').forEach(b=>b.remove());"
        "document.body.classList.remove('modal-open');"
        "document.body.style.removeProperty('overflow');"
        "document.body.style.removeProperty('padding-right');"
        "}",
        container,
    )
    logging.debug("Onboarding modal cleared")


def verify_modal_presence(page: Page):
    try:
        page.wait_for_selector("#FavModal", timeout=3000)
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
        logout_item = page.wait_for_selector("a[href*='logout']", timeout=5000)
        logout_item.click()
    except TimeoutError:
        pass
