import inspect
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src import cache, mlol
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
        page.locator.return_value.count.return_value = 0

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
            [
                mock.call("networkidle", timeout=15000),
                mock.call("networkidle", timeout=15000),
            ]
        )
        page.get_by_role.assert_called_once_with("link", name="Sfoglia online")
        sfoglia_button.click.assert_called_once()
        pressreader_page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    def test_dismiss_htmx_modals_clears_communication_modal(self):
        page = mock.Mock()
        communication_body = "#modal-communicationcontainer .modal-body"

        def wait_for_selector(selector, timeout):
            if selector == communication_body:
                return mock.Mock()
            raise PlaywrightTimeoutError("Timeout 3000ms exceeded.")

        page.wait_for_selector.side_effect = wait_for_selector

        mlol.dismiss_htmx_modals(page)

        page.wait_for_selector.assert_has_calls(
            [
                mock.call("#modal-onboardingontainer .modal-body", timeout=3000),
                mock.call(communication_body, timeout=3000),
            ]
        )
        page.locator.assert_called_once_with(
            "#modal-communicationcontainer [data-dismiss='modal']"
        )
        page.locator.return_value.first.click.assert_called_once_with(timeout=2000)
        page.evaluate.assert_called_once()
        assert page.evaluate.call_args.args[1] == "#modal-communicationcontainer"

    def test_dismiss_htmx_modal_skips_missing_close_buttons(self):
        page = mock.Mock()
        page.locator.return_value.first.count.return_value = 0

        mlol.dismiss_htmx_modal(page, "onboarding", "#modal-onboardingontainer")

        page.locator.return_value.first.click.assert_not_called()
        page.evaluate.assert_called_once()
        assert page.evaluate.call_args.args[1] == "#modal-onboardingontainer"

    def test_logout_follows_hidden_logout_anchor(self):
        page = mock.Mock()
        page.url = "https://example.medialibrary.it/media/details/1"
        logout_anchor = page.locator.return_value.first
        logout_anchor.get_attribute.return_value = "/login/logout"

        mlol.logout_mlol(page)

        page.locator.assert_called_once_with("a[href*='logout']")
        logout_anchor.get_attribute.assert_called_once_with("href", timeout=5000)
        page.goto.assert_called_once_with(
            "https://example.medialibrary.it/login/logout"
        )

    def test_logout_is_skipped_when_anchor_is_missing(self):
        page = mock.Mock()
        page.locator.return_value.first.get_attribute.side_effect = (
            PlaywrightTimeoutError("Timeout 5000ms exceeded.")
        )

        mlol.logout_mlol(page)

        page.goto.assert_not_called()

    def test_login_rejected_when_redirected_to_alert_page(self):
        page = mock.Mock()
        page.url = "https://example.medialibrary.it/alert"
        page.title.return_value = "Avviso - MLOL"

        assert mlol.login_was_rejected(page) is True

    def test_login_accepted_on_home_page(self):
        page = mock.Mock()
        page.url = "https://example.medialibrary.it/"
        page.title.return_value = "MLOL - Digital lending"

        assert mlol.login_was_rejected(page) is False

    @mock.patch("src.mlol.NOTIFIER")
    @mock.patch("src.mlol.chromium")
    def test_failed_login_procedure_exits_on_rejected_login(
        self, chromium_mock, notifier_mock
    ):
        page = mock.Mock()
        page.url = "https://example.medialibrary.it/alert"

        with self.assertRaises(SystemExit):
            mlol.failed_login_procedure(page)

        chromium_mock.clean.assert_called_once_with(debug_trace=True)
        notifier_mock.send_message.assert_called_once_with("Wrong MLOL credentials!")


def message_modal_page(message_id, text):
    page = mock.Mock()
    message_modal = page.wait_for_selector.return_value
    message_modal.get_attribute.return_value = message_id
    message_modal.inner_text.return_value = text
    return page


@mock.patch("src.mlol.NOTIFIER")
class TestMLOLMessageModal(TestCase):
    def setUp(self) -> None:
        self.temp_cache_dir = tempfile.TemporaryDirectory()
        modal_cache_patcher = mock.patch.object(
            cache, "ModalCache", cache.HashCache(Path(self.temp_cache_dir.name))
        )
        modal_cache_patcher.start()
        self.addCleanup(modal_cache_patcher.stop)
        self.addCleanup(self.temp_cache_dir.cleanup)

    def test_verify_modal_presence_uses_bounded_wait(self, notifier_mock):
        page = mock.Mock()
        page.wait_for_selector.side_effect = PlaywrightTimeoutError(
            "Timeout 3000ms exceeded."
        )

        mlol.verify_modal_presence(page)

        page.wait_for_selector.assert_called_once_with(
            "#modal-communicationcontainer .modal[id^='Message']",
            state="visible",
            timeout=3000,
        )
        notifier_mock.send_message.assert_not_called()
        notifier_mock.screenshot_client.take_screenshot.assert_not_called()

    def test_new_message_modal_notifies_with_text_and_screenshot(self, notifier_mock):
        page = message_modal_page(
            "Message258",
            "  Avviso dalla biblioteca\n\n La biblioteca   resterà chiusa.\n",
        )

        mlol.verify_modal_presence(page)

        page.wait_for_selector.return_value.get_attribute.assert_called_once_with("id")
        notifier_mock.send_message.assert_called_once_with(
            "New MLOL library message:\n"
            "Avviso dalla biblioteca La biblioteca resterà chiusa."
        )
        notifier_mock.screenshot_client.take_screenshot.assert_called_once_with(
            page, "mlol_message"
        )
        notifier_mock.screenshot_client.remove_screenshot.assert_called_once()
        page.locator.assert_not_called()
        page.wait_for_selector.return_value.click.assert_not_called()

    def test_seen_message_modal_is_not_notified_again(self, notifier_mock):
        page = message_modal_page("Message258", "Avviso dalla biblioteca")

        mlol.verify_modal_presence(page)
        mlol.verify_modal_presence(page)

        notifier_mock.send_message.assert_called_once()
        notifier_mock.screenshot_client.take_screenshot.assert_called_once()

    def test_new_message_id_is_notified_after_a_seen_one(self, notifier_mock):
        mlol.verify_modal_presence(message_modal_page("Message258", "Primo avviso"))
        mlol.verify_modal_presence(message_modal_page("Message259", "Secondo avviso"))

        assert notifier_mock.send_message.call_count == 2
        assert "Secondo avviso" in notifier_mock.send_message.call_args.args[0]

    def test_long_message_text_is_capped(self, notifier_mock):
        summary = mlol.summarize_modal_text("parola " * 200)

        assert len(summary) == 500
        assert summary.endswith("…")
        assert mlol.summarize_modal_text("breve avviso") == "breve avviso"


MESSAGE_MODAL_HTML = """
<div id="modal-onboardingontainer">
  <div class="modal fade show" id="onboarding" role="dialog" style="display: block;">
    <div class="modal-body">Benvenuto nella nuova MLOL</div>
  </div>
</div>
<div id="modal-communicationcontainer">
  <div class="modal fade show" id="Message258" role="dialog"
       aria-labelledby="Message258Label" style="display: block;">
    <div class="modal-dialog"><div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="Message258Label">Avviso dalla biblioteca</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"
                aria-label="Chiudi"></button>
      </div>
      <div class="modal-body"><p>La biblioteca resterà
        chiusa il 25 dicembre.</p></div>
    </div></div>
  </div>
</div>
"""

ONBOARDING_ONLY_HTML = """
<div id="modal-onboardingontainer">
  <div class="modal fade show" id="onboarding" role="dialog" style="display: block;">
    <div class="modal-body">Benvenuto nella nuova MLOL</div>
  </div>
</div>
<div id="modal-communicationcontainer"></div>
"""

HIDDEN_MESSAGE_HTML = """
<div id="modal-communicationcontainer">
  <div class="modal fade" id="Message258" role="dialog" style="display: none;">
    <div class="modal-body">Avviso dalla biblioteca</div>
  </div>
</div>
"""


@mock.patch("src.mlol.cache.should_notify_modal", return_value=True)
@mock.patch("src.mlol.NOTIFIER")
class TestMLOLMessageModalSelector(TestCase):
    @mock.patch("src.notify.Notifier")
    def setUp(self, notifier_mock) -> None:
        self.chromium = Chromium(notifier=notifier_mock, trace=False)
        self.page = self.chromium.context.new_page()

    def tearDown(self) -> None:
        self.chromium.clean()

    def test_library_message_modal_is_detected(self, notifier_mock, should_notify_mock):
        self.page.set_content(MESSAGE_MODAL_HTML)

        mlol.verify_modal_presence(self.page)

        should_notify_mock.assert_called_once_with("Message258")
        notifier_mock.send_message.assert_called_once_with(
            "New MLOL library message:\n"
            "Avviso dalla biblioteca La biblioteca resterà chiusa il 25 dicembre."
        )

    @mock.patch("src.mlol.MLOL_MESSAGE_MODAL_TIMEOUT", 200)
    def test_other_modals_are_ignored(self, notifier_mock, should_notify_mock):
        for html in (ONBOARDING_ONLY_HTML, HIDDEN_MESSAGE_HTML):
            with self.subTest(html=html):
                self.page.set_content(html)

                mlol.verify_modal_presence(self.page)

        should_notify_mock.assert_not_called()
        notifier_mock.send_message.assert_not_called()


def locator_with_counts(counts):
    def locator(selector):
        return mock.Mock(**{"count.return_value": counts.get(selector, 0)})

    return locator


class TestAltchaGate(TestCase):
    def test_pass_altcha_gate_skips_pages_without_gate(self):
        page = mock.Mock()
        page.locator.side_effect = locator_with_counts({})

        mlol.pass_altcha_gate(page)

        page.locator.assert_called_once_with("#altcha-gate")
        page.wait_for_selector.assert_not_called()

    def test_pass_altcha_gate_waits_for_gate_to_detach(self):
        page = mock.Mock()
        page.locator.side_effect = locator_with_counts({"#altcha-gate": 1})

        mlol.pass_altcha_gate(page)

        page.wait_for_selector.assert_called_once_with(
            "#altcha-gate", state="detached", timeout=60000
        )
        page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    def test_pass_altcha_gate_raises_when_gate_does_not_clear(self):
        page = mock.Mock()
        page.locator.side_effect = locator_with_counts({"#altcha-gate": 1})
        page.wait_for_selector.side_effect = PlaywrightTimeoutError(
            "Timeout 60000ms exceeded."
        )

        with self.assertRaisesRegex(Exception, "ALTCHA gate did not clear"):
            mlol.pass_altcha_gate(page)

    def test_pass_altcha_gate_raises_when_cookies_are_disabled(self):
        page = mock.Mock()
        page.locator.side_effect = locator_with_counts(
            {"#altcha-gate": 1, "#altcha-nocookie:not([hidden])": 1}
        )

        with self.assertRaisesRegex(Exception, "requires cookies"):
            mlol.pass_altcha_gate(page)

        page.wait_for_selector.assert_not_called()

    def test_goto_mlol_passes_gate_before_waiting_for_network(self):
        page = mock.Mock()
        page.locator.side_effect = locator_with_counts({"#altcha-gate": 1})

        mlol.goto_mlol(page, "https://milano.medialibrary.it/search?idtype=600")

        page.goto.assert_called_once_with(
            "https://milano.medialibrary.it/search?idtype=600"
        )
        assert page.method_calls.index(
            mock.call.wait_for_selector("#altcha-gate", state="detached", timeout=60000)
        ) < page.method_calls.index(
            mock.call.wait_for_load_state("networkidle", timeout=15000)
        )

    def test_wait_for_network_idle_is_best_effort(self):
        page = mock.Mock()
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError(
            "Timeout 15000ms exceeded."
        )

        mlol.wait_for_network_idle(page)

        page.wait_for_load_state.assert_called_once_with("networkidle", timeout=15000)

    def test_missing_corriere_error_reports_listing_state(self):
        page = mock.Mock()
        page.url = "https://milano.medialibrary.it/"
        page.eval_on_selector_all.return_value = None
        page.locator.side_effect = locator_with_counts({})
        page.title.return_value = "Verifica di sicurezza"

        with self.assertRaisesRegex(
            Exception, r"\(0 titles on page 'Verifica di sicurezza'\)"
        ):
            mlol.navigate_to_newspapers.__wrapped__(page)


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
