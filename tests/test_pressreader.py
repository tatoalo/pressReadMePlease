from http import HTTPStatus
from unittest import TestCase, mock
from datetime import datetime
from pathlib import Path

from src.chromium import Chromium
from src.pressreader import subscribe_to_login_event, verify_execution_flow
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

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.sys.exit")
    def test_access_forbidden_login_is_captured(
        self, system_exit_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        notifier_send_message_argument = "notifier_send_message_has_been_called"
        system_exit_mock.return_value = "system_exit_message"
        clean_mock.clean.return_value = "mocking clean call"

        global_notifier_mock.send_message.return_value = notifier_send_message_argument
        mocked_resource_url = "https://www.example.com/Authentication/SignIn"

        self.page.route(
            "**/Authentication/SignIn",
            lambda route: route.fulfill(status=HTTPStatus.FORBIDDEN),
        )

        subscribe_to_login_event(self.page)
        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert len(global_notifier_mock.send_message.call_args_list) == 1
        assert (
            "access denied"
            in str(global_notifier_mock.send_message.call_args_list[0]).lower()
        )
        assert global_notifier_mock.send_message.called

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    def test_access_forbidden_not_captured_with_different_endpoint(
        self, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        resource_url_not_routed = "https://www.example.com/ThisIsGoingToBeA404"

        subscribe_to_login_event(self.page)
        self.chromium.visit_site(page=self.page, url=resource_url_not_routed)

        assert global_notifier_mock.called is False

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.locator")
    def test_access_information_retrieved_correctly(
        self, page_html_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_html_mock.return_value.inner_text.return_value = (
            "Complimentary access: 2 days"
        )

        mocked_resource_url = "https://www.example.com/catalog"

        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert verify_execution_flow(self.page)[0] is True

    @mock.patch("src.pressreader.NOTIFIER")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.locator")
    def test_access_information_retrieved_signifies_wrong_execution_flow(
        self, page_html_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_html_mock.return_value.inner_text.return_value = (
            "Complimentary access: 4 days"
        )

        mocked_resource_url = "https://www.example.com/catalog"

        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert verify_execution_flow(self.page)[0] is False


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
    @mock.patch("src.CORRECT_FLOW_DAYS_RESET", 2)
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
    @mock.patch("src.CORRECT_FLOW_DAYS_RESET", 2)
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
    @mock.patch("src.CORRECT_FLOW_DAYS_RESET", 2)
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
    @mock.patch("src.CORRECT_FLOW_DAYS_RESET", 2)
    def test_should_execute_flow_returns_true_when_exactly_enough_days_passed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 3, 10, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, True)

        result = should_execute_flow()

        assert result is True

    @mock.patch("src.utilities._last_execution_time")
    @mock.patch("src.utilities.datetime")
    @mock.patch("src.CORRECT_FLOW_DAYS_RESET", 2)
    def test_should_execute_flow_returns_true_when_last_execution_failed(
        self, datetime_mock, last_execution_mock
    ):
        last_datetime = datetime(2025, 1, 1, 10, 0, 0)
        current_datetime = datetime(2025, 1, 1, 11, 0, 0)
        datetime_mock.now.return_value = current_datetime
        last_execution_mock.return_value = (last_datetime, False)

        result = should_execute_flow()

        assert result is True

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
