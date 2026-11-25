from http import HTTPStatus
from unittest import TestCase, mock
from datetime import datetime
from pathlib import Path

from src.chromium import Chromium
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.pressreader import (
    is_sign_in_response,
    login_pressreader,
    logout_pressreader,
    subscribe_to_login_event,
    verify_execution_flow,
    wait_for_login_outcome,
)
from src.utilities import (
    should_execute_flow,
    _last_execution_time,
    update_last_execution_time,
)


class TestPressreader(TestCase):
    @mock.patch("src.notify.Notifier")
    def setUp(self, notifier_mock) -> None:
        self.chromium = Chromium(notifier=notifier_mock, trace=False)
        self.chromium.context.new_page()
        self.page = self.chromium.context.pages[0]
        self.page.goto("https:///www.google.com")

    def test_sign_in_endpoints_are_recognised(self):
        sign_in_urls = (
            "https://ingress.pressreader.com/services/auth/Signin",
            "https://www.pressreader.com/authentication/v1/signIn",
            "https://www.pressreader.com/Authentication/SignIn?returnUrl=%2Fcatalog",
        )
        for url in sign_in_urls:
            with self.subTest(url=url):
                assert is_sign_in_response(mock.Mock(url=url)) is True

        other_urls = (
            "https://www.pressreader.com/catalog",
            "https://www.pressreader.com/signin-help",
            "https://ingress.pressreader.com/services/auth/Signout",
        )
        for url in other_urls:
            with self.subTest(url=url):
                assert is_sign_in_response(mock.Mock(url=url)) is False

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_access_forbidden_sign_in_is_recorded(
        self, chromium_mock, global_notifier_mock
    ):
        sign_in_urls = (
            "https://ingress.pressreader.com/services/auth/Signin",
            "https://www.pressreader.com/authentication/v1/signIn",
        )
        for url in sign_in_urls:
            self.page.route(
                url, lambda route: route.fulfill(status=HTTPStatus.FORBIDDEN)
            )

        sign_in_statuses = subscribe_to_login_event(self.page)
        for url in sign_in_urls:
            self.page.goto(url)

        assert sign_in_statuses == [HTTPStatus.FORBIDDEN, HTTPStatus.FORBIDDEN]
        global_notifier_mock.send_message.assert_not_called()
        chromium_mock.clean.assert_not_called()

    def test_access_forbidden_not_recorded_with_different_endpoint(self):
        self.page.route(
            "**/catalog", lambda route: route.fulfill(status=HTTPStatus.FORBIDDEN)
        )

        sign_in_statuses = subscribe_to_login_event(self.page)
        self.page.goto("https://www.pressreader.com/catalog")

        assert sign_in_statuses == []

    @mock.patch("src.pressreader.LOGIN_OUTCOME_TIMEOUT", 500)
    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_login_outcome_exits_when_sign_in_was_forbidden(
        self, chromium_mock, global_notifier_mock
    ):
        events = mock.Mock()
        events.attach_mock(global_notifier_mock.send_message, "send_message")
        events.attach_mock(chromium_mock.clean, "clean")
        self.page.set_content("<div>Something went wrong</div>")

        with self.assertRaises(SystemExit) as raised:
            wait_for_login_outcome(self.page, [HTTPStatus.FORBIDDEN])

        assert raised.exception.code == "Access denied to PressReader!"
        global_notifier_mock.send_message.assert_called_once()
        assert (
            "Access denied to PressReader"
            in global_notifier_mock.send_message.call_args.args[0]
        )
        assert [name for name, _, _ in events.mock_calls] == ["send_message", "clean"]
        chromium_mock.clean.assert_called_once_with(debug_trace=True)

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_login_outcome_continues_on_forbidden_sign_in_when_signed_in(
        self, chromium_mock, global_notifier_mock
    ):
        self.page.set_content("<span class='userphoto-title'>AB</span>")

        with self.assertLogs(level="WARNING") as logs:
            wait_for_login_outcome(self.page, [HTTPStatus.OK, HTTPStatus.FORBIDDEN])

        assert "403" in logs.output[0]
        global_notifier_mock.send_message.assert_not_called()
        chromium_mock.clean.assert_not_called()

    @mock.patch("src.pressreader.wait_for_login_outcome")
    def test_login_subscribes_to_sign_in_responses_before_submitting(
        self, wait_for_login_outcome_mock
    ):
        page = mock.Mock()
        stay_signed_in_checkbox = mock.Mock()
        stay_signed_in_checkbox.is_checked.return_value = False
        submit_button = mock.Mock()
        page.attach_mock(submit_button, "submit_button")
        page.wait_for_selector.side_effect = [stay_signed_in_checkbox, submit_button]

        login_pressreader.__wrapped__(page, ("username", "password"))

        call_names = [name for name, _, _ in page.mock_calls]
        assert call_names.index("on") < call_names.index("submit_button.click")
        assert page.on.call_args.args[0] == "response"
        sign_in_statuses = wait_for_login_outcome_mock.call_args.args[1]
        wait_for_login_outcome_mock.assert_called_once_with(page, sign_in_statuses)
        assert sign_in_statuses == []

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.locator")
    def test_access_information_retrieved_correctly(
        self, page_html_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_html_mock.return_value.inner_text.return_value = (
            "Reconnect when access expires — 2 days 23 hours left"
        )

        mocked_resource_url = "https://www.example.com/catalog"

        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert verify_execution_flow(self.page) == (True, 2, None)
        global_notifier_mock.send_message.assert_not_called()
        global_notifier_mock.screenshot_client.take_screenshot.assert_not_called()

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.locator")
    def test_access_information_retrieved_signifies_wrong_execution_flow(
        self, page_html_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_html_mock.return_value.inner_text.return_value = (
            "Reconnect when access expires — 1 day 23 hours left"
        )

        mocked_resource_url = "https://www.example.com/catalog"

        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert verify_execution_flow(self.page)[0] is False

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.get_by_text")
    @mock.patch("src.pressreader.Page.locator")
    def test_sponsored_access_fallback_succeeds(
        self, page_locator_mock, page_get_by_text_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_locator_mock.return_value.inner_text.side_effect = PlaywrightTimeoutError(
            "Timeout 30000ms exceeded."
        )
        page_get_by_text_mock.return_value.wait_for.return_value = None

        result = verify_execution_flow(self.page)

        assert result[0] is True
        assert result[1] == 2
        global_notifier_mock.send_message.assert_not_called()
        global_notifier_mock.screenshot_client.take_screenshot.assert_not_called()

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.get_by_text")
    @mock.patch("src.pressreader.Page.locator")
    def test_no_free_access_and_no_sponsored_access_fails(
        self, page_locator_mock, page_get_by_text_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_locator_mock.return_value.inner_text.side_effect = PlaywrightTimeoutError(
            "Timeout 30000ms exceeded."
        )
        page_get_by_text_mock.return_value.wait_for.side_effect = (
            PlaywrightTimeoutError("Timeout 5000ms exceeded.")
        )
        page_locator_mock.return_value.first.wait_for.side_effect = (
            PlaywrightTimeoutError("Timeout 5000ms exceeded.")
        )

        result = verify_execution_flow(self.page)

        assert result[0] is False
        assert result[1] is None
        assert "Could not find free access time element" in result[2]
        global_notifier_mock.send_message.assert_not_called()

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.get_by_text")
    @mock.patch("src.pressreader.Page.locator")
    def test_authenticated_session_fallback_succeeds(
        self, page_locator_mock, page_get_by_text_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_locator_mock.return_value.inner_text.side_effect = PlaywrightTimeoutError(
            "Timeout 30000ms exceeded."
        )
        page_get_by_text_mock.return_value.wait_for.side_effect = (
            PlaywrightTimeoutError("Timeout 5000ms exceeded.")
        )
        page_locator_mock.return_value.first.wait_for.return_value = None

        with self.assertLogs(level="WARNING") as logs:
            result = verify_execution_flow(self.page)

        assert result == (True, 2, None)
        assert "could not be confirmed" in logs.output[0]
        global_notifier_mock.send_message.assert_called_once_with(
            "PressReader access could not be confirmed: "
            "signed in, but no countdown or sponsor banner found"
        )
        global_notifier_mock.screenshot_client.take_screenshot.assert_called_once_with(
            self.page, "unconfirmed_access"
        )
        global_notifier_mock.screenshot_client.remove_screenshot.assert_called_once()

    @mock.patch("src.pressreader.Page.wait_for_selector")
    @mock.patch("src.pressreader.Page.locator")
    def test_logout_uses_locator_clicks(
        self, page_locator_mock, page_wait_for_selector_mock
    ):
        hotspot_dialog_locator = mock.Mock()
        first_locator = mock.Mock()
        second_locator = mock.Mock()
        page_locator_mock.side_effect = [
            mock.Mock(first=hotspot_dialog_locator),
            mock.Mock(first=first_locator),
            mock.Mock(first=second_locator),
        ]

        logout_pressreader(self.page)

        page_wait_for_selector_mock.assert_not_called()
        assert page_locator_mock.call_count == 3
        hotspot_dialog_locator.click.assert_called_once_with(timeout=2000)
        first_locator.click.assert_called_once_with(timeout=5000)
        second_locator.click.assert_called_once_with(timeout=5000)

    @mock.patch("src.pressreader.Page.locator")
    def test_logout_continues_when_hotspot_dialog_is_absent(self, page_locator_mock):
        hotspot_dialog_locator = mock.Mock()
        hotspot_dialog_locator.click.side_effect = PlaywrightTimeoutError(
            "Timeout 2000ms exceeded."
        )
        first_locator = mock.Mock()
        second_locator = mock.Mock()
        page_locator_mock.side_effect = [
            mock.Mock(first=hotspot_dialog_locator),
            mock.Mock(first=first_locator),
            mock.Mock(first=second_locator),
        ]

        logout_pressreader(self.page)

        first_locator.click.assert_called_once_with(timeout=5000)
        second_locator.click.assert_called_once_with(timeout=5000)

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_login_outcome_succeeds_when_signed_in(
        self, chromium_mock, global_notifier_mock
    ):
        self.page.set_content("<span class='userphoto-title'>AB</span>")

        wait_for_login_outcome(self.page, [HTTPStatus.OK])

        chromium_mock.clean.assert_not_called()
        global_notifier_mock.send_message.assert_not_called()

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_login_outcome_exits_on_wrong_credentials(
        self, chromium_mock, global_notifier_mock
    ):
        self.page.set_content("<div class='infomsg'>Invalid username or password</div>")

        with self.assertRaises(SystemExit):
            wait_for_login_outcome(self.page, [])

        chromium_mock.clean.assert_called_once_with(debug_trace=True)
        global_notifier_mock.send_message.assert_called_once_with(
            "Wrong Pressreader credentials!"
        )

    @mock.patch("src.pressreader.LOGIN_OUTCOME_TIMEOUT", 500)
    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_login_outcome_fails_when_sign_in_never_completes(
        self, chromium_mock, global_notifier_mock
    ):
        self.page.set_content(
            "<div class='infomsg'>Reconnect when access expires</div>"
            "<div>This issue brought to you by</div>"
        )

        with self.assertRaises(Exception) as raised:
            wait_for_login_outcome(self.page, [HTTPStatus.OK])

        assert "sign-in did not complete" in str(raised.exception)
        global_notifier_mock.send_message.assert_not_called()
        chromium_mock.clean.assert_not_called()


class TestUtilities(TestCase):
    def setUp(self) -> None:
        self.test_log_file = Path("running_log.txt")
        if self.test_log_file.exists():
            self.test_log_file.unlink()

    def tearDown(self) -> None:
        if self.test_log_file.exists():
            self.test_log_file.unlink()

    @mock.patch("src.utilities.dump")
    @mock.patch("src.utilities.Path")
    def test_last_execution_time_creates_empty_file_and_returns_none_when_file_doesnt_exist(
        self, path_mock, dump_mock
    ):
        path_mock.return_value.exists.return_value = False

        mock_file = mock.mock_open()
        path_mock.return_value.open = mock_file

        result = _last_execution_time()

        assert result is None
        dump_mock.assert_called_once()
        call_args = dump_mock.call_args[0]
        assert call_args[0] == {}

    @mock.patch("src.utilities.Path")
    @mock.patch("src.utilities.load")
    def test_last_execution_time_returns_tuple_when_file_exists(
        self, load_mock, path_mock
    ):
        path_mock.return_value.exists.return_value = True
        expected_datetime = datetime(2025, 1, 1, 10, 0, 0)
        load_mock.return_value = {
            "last_execution_time": expected_datetime.isoformat(),
            "successful": True,
        }

        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            result = _last_execution_time()

        assert result == (expected_datetime, True)

    @mock.patch("src.utilities.Path")
    @mock.patch("src.utilities.load")
    def test_last_execution_time_returns_tuple_with_failed_status(
        self, load_mock, path_mock
    ):
        path_mock.return_value.exists.return_value = True
        expected_datetime = datetime(2025, 1, 1, 10, 0, 0)
        load_mock.return_value = {
            "last_execution_time": expected_datetime.isoformat(),
            "successful": False,
        }

        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            result = _last_execution_time()

        assert result == (expected_datetime, False)

    @mock.patch("src.utilities.Path")
    @mock.patch("src.utilities.load")
    def test_last_execution_time_returns_none_when_value_missing(
        self, load_mock, path_mock
    ):
        path_mock.return_value.exists.return_value = True
        load_mock.return_value = {}

        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            result = _last_execution_time()

        assert result is None

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.ACCESS_RENEW_EVERY_DAYS", 2)
    def test_should_execute_flow_returns_true_when_no_last_execution(
        self, datetime_mock, last_execution_mock
    ):
        current_datetime = datetime(2025, 1, 5, 10, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = None

        result = should_execute_flow()

        assert result is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.ACCESS_RENEW_EVERY_DAYS", 2)
    def test_should_execute_flow_returns_true_when_enough_days_passed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 4, 10, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, True)

        result = should_execute_flow()

        assert result is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.ACCESS_RENEW_EVERY_DAYS", 2)
    def test_should_execute_flow_returns_false_when_not_enough_days_passed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 2, 9, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, True)

        result = should_execute_flow()

        assert result is False

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.ACCESS_RENEW_EVERY_DAYS", 2)
    def test_should_execute_flow_returns_true_when_exactly_enough_calendar_days_passed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 3, 9, 59, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, True)

        result = should_execute_flow()

        assert result is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.ACCESS_RENEW_EVERY_DAYS", 2)
    def test_should_execute_flow_returns_true_when_last_execution_failed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 1, 11, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, False)

        result = should_execute_flow()

        assert result is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    def test_should_execute_flow_runs_after_two_days_despite_time_drift(
        self, datetime_mock, last_execution_mock
    ):
        datetime_mock.now.return_value = datetime(2026, 10, 16, 3, 20, 2)
        last_execution_mock.return_value = (datetime(2026, 10, 14, 3, 21), True)

        assert should_execute_flow() is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    def test_should_execute_flow_skips_after_yesterday_success(
        self, datetime_mock, last_execution_mock
    ):
        datetime_mock.now.return_value = datetime(2026, 10, 16, 3, 20, 2)
        last_execution_mock.return_value = (datetime(2026, 10, 15, 3, 21), True)

        assert should_execute_flow() is False

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    def test_should_execute_flow_skips_after_success_earlier_today(
        self, datetime_mock, last_execution_mock
    ):
        datetime_mock.now.return_value = datetime(2026, 10, 16, 9, 35)
        last_execution_mock.return_value = (datetime(2026, 10, 16, 3, 21), True)

        assert should_execute_flow() is False

    @mock.patch("src.utilities.datetime")
    @mock.patch("src.utilities.dump")
    def test_update_last_execution_time_writes_datetime_and_success_status(
        self, dump_mock, datetime_mock
    ):
        current_datetime = datetime(2025, 1, 5, 14, 30, 0)
        datetime_mock.now.return_value = current_datetime

        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            update_last_execution_time(successful=True)

        dump_mock.assert_called_once()
        call_args = dump_mock.call_args[0]
        assert call_args[0]["last_execution_time"] == current_datetime.isoformat()
        assert call_args[0]["successful"] is True

    @mock.patch("src.utilities.datetime")
    @mock.patch("src.utilities.dump")
    def test_update_last_execution_time_writes_failed_status(
        self, dump_mock, datetime_mock
    ):
        current_datetime = datetime(2025, 1, 5, 14, 30, 0)
        datetime_mock.now.return_value = current_datetime

        mock_file = mock.mock_open()
        with mock.patch("builtins.open", mock_file):
            update_last_execution_time(successful=False)

        dump_mock.assert_called_once()
        call_args = dump_mock.call_args[0]
        assert call_args[0]["last_execution_time"] == current_datetime.isoformat()
        assert call_args[0]["successful"] is False
