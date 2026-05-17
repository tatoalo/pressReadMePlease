import inspect
from pathlib import Path
from unittest import TestCase, mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src import mlol
from src.chromium import Chromium


class TestMLOLRedesign(TestCase):
    @mock.patch("src.mlol.failed_login_procedure")
    def test_perform_login_clicks_accedi_on_clean_page(self, failed_login_mock):
        page = mock.Mock()
        page.url = "https://milano.medialibrary.it/"
        accedi_button = mock.Mock()
        page.get_by_role.return_value.first = accedi_button
        page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("Timeout 1000ms exceeded."),
            mock.Mock(),
        ]

        mlol.perform_login(page, ("username", "password"))

        page.goto.assert_not_called()
        page.get_by_role.assert_called_once_with("button", name="Accedi")
        accedi_button.click.assert_called_once_with(timeout=5000)
        page.wait_for_selector.assert_has_calls(
            [
                mock.call("#Username", timeout=1000),
                mock.call("#Username", timeout=5000),
            ]
        )
        page.fill.assert_has_calls(
            [
                mock.call("#Username", "username"),
                mock.call("#Password", "password"),
            ]
        )
        for fill_call in page.fill.call_args_list:
            assert "timeout" not in fill_call.kwargs
        page.press.assert_called_once_with("#Password", "Enter")
        page.wait_for_load_state.assert_called_once_with("domcontentloaded")
        failed_login_mock.assert_called_once_with(page)

    @mock.patch("src.mlol.failed_login_procedure")
    def test_perform_login_fills_existing_login_page(self, failed_login_mock):
        page = mock.Mock()
        page.url = "https://milano.medialibrary.it/login/login"
        page.wait_for_selector.return_value = mock.Mock()

        mlol.perform_login(page, ("username", "password"))

        page.get_by_role.assert_not_called()
        page.goto.assert_not_called()
        page.fill.assert_has_calls(
            [
                mock.call("#Username", "username"),
                mock.call("#Password", "password"),
            ]
        )
        failed_login_mock.assert_called_once_with(page)

    @mock.patch("src.mlol.failed_login_procedure")
    def test_perform_login_falls_back_to_login_page_when_accedi_unavailable(
        self, failed_login_mock
    ):
        page = mock.Mock()
        page.url = "https://milano.medialibrary.it/home/index.aspx"
        accedi_button = mock.Mock()
        accedi_button.click.side_effect = PlaywrightTimeoutError(
            "Timeout 5000ms exceeded."
        )
        page.get_by_role.return_value.first = accedi_button
        page.wait_for_selector.side_effect = PlaywrightTimeoutError(
            "Timeout 1000ms exceeded."
        )

        mlol.perform_login(page, ("username", "password"))

        page.goto.assert_called_once_with("https://milano.medialibrary.it/login/login")
        page.get_by_role.assert_called_once_with("button", name="Accedi")
        page.fill.assert_has_calls(
            [
                mock.call("#Username", "username"),
                mock.call("#Password", "password"),
            ]
        )
        page.wait_for_load_state.assert_has_calls(
            [mock.call("domcontentloaded"), mock.call("domcontentloaded")]
        )
        failed_login_mock.assert_called_once_with(page)

    def test_navigate_to_newspapers_uses_edicola_category_and_sfoglia_link(self):
        page = mock.Mock()
        page.url = "https://milano.medialibrary.it/login/login"
        page.eval_on_selector_all.return_value = "/media/details/550276273"

        sfoglia_button = mock.Mock()
        page.get_by_role.return_value.first = sfoglia_button

        pressreader_page = mock.Mock()
        pressreader_page.title.return_value = "PressReader - Corriere della Sera"
        page_info = mock.Mock(value=pressreader_page)
        expect_page_context = mock.MagicMock()
        expect_page_context.__enter__.return_value = page_info

        previous_chromium = mlol.chromium
        mlol.chromium = mock.Mock()
        mlol.chromium.context.expect_page.return_value = expect_page_context
        try:
            result = mlol.navigate_to_newspapers(page)
        finally:
            mlol.chromium = previous_chromium

        assert result is pressreader_page
        page.goto.assert_has_calls(
            [
                mock.call("https://milano.medialibrary.it/search?idtype=600"),
                mock.call("https://milano.medialibrary.it/media/details/550276273"),
            ]
        )
        page.wait_for_load_state.assert_has_calls(
            [mock.call("networkidle"), mock.call("networkidle")]
        )
        page.get_by_role.assert_called_once_with("link", name="Sfoglia online")
        sfoglia_button.click.assert_called_once()
        pressreader_page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    def test_verify_modal_presence_uses_bounded_wait(self):
        page = mock.Mock()
        page.wait_for_selector.side_effect = PlaywrightTimeoutError(
            "Timeout 3000ms exceeded."
        )

        mlol.verify_modal_presence(page)

        page.wait_for_selector.assert_called_once_with("#FavModal", timeout=3000)

    def test_logout_uses_redesigned_logout_anchor(self):
        page = mock.Mock()
        logout_item = mock.Mock()
        page.wait_for_selector.return_value = logout_item

        mlol.logout_mlol(page)

        page.wait_for_selector.assert_called_once_with(
            "a[href*='logout']", timeout=5000
        )
        logout_item.click.assert_called_once()


class TestTimeoutSafety(TestCase):
    def test_chromium_default_timeout_is_bounded(self):
        timeout_parameter = inspect.signature(Chromium.__init__).parameters["timeout"]

        assert timeout_parameter.default == 60000

    def test_no_infinite_playwright_timeouts_in_source(self):
        offenders = []
        for path in Path("src").glob("*.py"):
            if "timeout=0" in path.read_text():
                offenders.append(str(path))

        assert offenders == []
