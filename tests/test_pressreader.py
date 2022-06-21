from http import HTTPStatus
from re import sub
from unittest import TestCase, mock

from src.chromium import Chromium
from src.pressreader import subscribe_to_login_event


class TestPressreader(TestCase):
    @mock.patch("src.notify.Notifier")
    def setUp(self, notifier_mock) -> None:
        self.chromium = Chromium(notifier=notifier_mock, trace=False)
        self.chromium.context.new_page()
        self.page = self.chromium.context.pages[0]
        self.page.goto("https:///www.google.com")

    @mock.patch("src.pressreader.NOTIFY")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.sys.exit")
    def test_access_forbidden_login_is_captured(
        self, system_exit_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        notifier_send_message_argument = "notifier_send_message_has_been_called"
        system_exit_mock.return_value = "system_exit_message"

        global_notifier_mock.send_message.return_value = notifier_send_message_argument
        mocked_resource_url = "https://www.example.com/Authentication/SignIn"

        self.page.route(
            "**/Authentication/SignIn",
            lambda route: route.fulfill(status=HTTPStatus.FORBIDDEN),
        )

        subscribe_to_login_event(self.page)
        self.page.goto(mocked_resource_url)

        assert len(global_notifier_mock.send_message.call_args_list) == 1
        assert (
            "access denied"
            in str(global_notifier_mock.send_message.call_args_list[0]).lower()
        )
        assert global_notifier_mock.send_message.called

    @mock.patch("src.pressreader.NOTIFY")
    def test_access_forbidden_not_captured_with_different_endpoint(
        self, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        resource_url_not_routed = "https://www.example.com/ThisIsGoingToBeA404"

        subscribe_to_login_event(self.page)
        self.page.goto(resource_url_not_routed)

        assert global_notifier_mock.called == False
