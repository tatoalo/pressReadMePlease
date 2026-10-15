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
MLOL_LISTING_SELECTOR = "a[href*='/media/details/']"

ALTCHA_GATE_SELECTOR = "#altcha-gate"
ALTCHA_NOCOOKIE_SELECTOR = "#altcha-nocookie:not([hidden])"
ALTCHA_TIMEOUT = 60000

MLOL_NETWORK_IDLE_TIMEOUT = 15000


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

    goto_mlol(page, urljoin(mlol_base_url, "/search?idtype=600"))

    corriere_href = page.eval_on_selector_all(
        MLOL_LISTING_SELECTOR,
        "els=>{for(const e of els){"
        "if((e.innerText||'').trim().toLowerCase()==='corriere della sera')"
        "return e.getAttribute('href');}return null;}",
    )
    if not corriere_href:
        listing_count = page.locator(MLOL_LISTING_SELECTOR).count()
        raise Exception(
            "Corriere della Sera not found in Edicola listing "
            f"({listing_count} titles on page '{page.title()}')"
        )

    goto_mlol(page, urljoin(mlol_base_url, corriere_href))

    dismiss_htmx_modals(page)

    sfoglia_button = page.get_by_role("link", name="Sfoglia online").first

    with chromium.context.expect_page() as pressreader_blank_target:
        sfoglia_button.click()
    page_pressreader = pressreader_blank_target.value
    page_pressreader.wait_for_load_state("domcontentloaded")

    assert "pressreader" in page_pressreader.title().lower(), Exception(
        "Failed tab switch"
    )

    return page_pressreader


def goto_mlol(page: Page, url: str) -> None:
    page.goto(url)
    pass_altcha_gate(page)
    wait_for_network_idle(page)


def wait_for_network_idle(page: Page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=MLOL_NETWORK_IDLE_TIMEOUT)
    except TimeoutError:
        logging.debug(
            f"MLOL network not idle after {MLOL_NETWORK_IDLE_TIMEOUT // 1000}s, "
            "continuing"
        )


def pass_altcha_gate(page: Page) -> None:
    if page.locator(ALTCHA_GATE_SELECTOR).count() == 0:
        return

    logging.debug("ALTCHA gate detected - waiting for verification")
    if page.locator(ALTCHA_NOCOOKIE_SELECTOR).count() > 0:
        raise Exception("ALTCHA gate requires cookies, verification cannot start")

    try:
        page.wait_for_selector(
            ALTCHA_GATE_SELECTOR, state="detached", timeout=ALTCHA_TIMEOUT
        )
    except TimeoutError:
        raise Exception(f"ALTCHA gate did not clear within {ALTCHA_TIMEOUT // 1000}s")

    page.wait_for_load_state("domcontentloaded")
    logging.debug("ALTCHA gate cleared")


HTMX_MODAL_CONTAINERS = (
    ("onboarding", "#modal-onboardingontainer"),
    ("communication", "#modal-communicationcontainer"),
)


def dismiss_htmx_modals(page: Page):
    for name, container in HTMX_MODAL_CONTAINERS:
        dismiss_htmx_modal(page, name, container)


def dismiss_htmx_modal(page: Page, name: str, container: str):
    try:
        page.wait_for_selector(f"{container} .modal-body", timeout=3000)
    except TimeoutError:
        return

    logging.debug(f"{name.capitalize()} modal detected - dismissing")

    close_selectors = (
        f"{container} [data-dismiss='modal']",
        f"{container} [data-bs-dismiss='modal']",
        f"{container} .btn-close",
        f"{container} button.close",
    )
    for selector in close_selectors:
        try:
            page.locator(selector).first.click(timeout=2000)
            logging.debug(f"{name.capitalize()} modal dismissed via {selector}")
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
    logging.debug(f"{name.capitalize()} modal cleared")


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
