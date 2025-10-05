from playwright.sync_api import Page

from chromium import Chromium
from mlol import visit_MLOL
from pressreader import visit_pressreader
from src import CONFIGURATION, NOTIFIER, TIMEOUT, logging
from utilities import should_execute_flow, update_last_execution_time


def config_page(page: Page):
    window_size = {"width": 1920, "height": 1080}
    page.wait_for_load_state()
    page.set_viewport_size(viewport_size=window_size)
    page.set_default_timeout(TIMEOUT)


def main():
    if not should_execute_flow():
        logging.debug("*** Automation flow not executed ***")
        return

    mlol_link = CONFIGURATION.mlol_website
    mlol_credentials = (
        CONFIGURATION.mlol_username,
        CONFIGURATION.mlol_password,
    )
    pressreader_credentials = (
        CONFIGURATION.pressreader_username,
        CONFIGURATION.pressreader_password,
    )

    try:
        chromium = Chromium(
            headless=True, trace=True, timeout=TIMEOUT, notifier=NOTIFIER
        )
        chromium.context.on("page", config_page)
        chromium.context.new_page()
        pressreader_tab = visit_MLOL(
            mlol_entrypoint=mlol_link, mlol_auth=mlol_credentials
        )

        visit_pressreader(
            page=pressreader_tab,
            pressreader_auth=pressreader_credentials,
        )
        logging.debug("*** Automation flow has terminated correctly ***")
        update_last_execution_time(successful=True)
        chromium.clean()
    except SystemExit as e:
        logging.debug(f"*** Automation flow failed: {e} ***")
        update_last_execution_time(successful=False)
        raise


if __name__ == "__main__":
    main()
