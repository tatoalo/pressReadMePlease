from http import HTTPStatus
from unittest import TestCase, mock

from src.chromium import Chromium
from src.pressreader import subscribe_to_login_event, verify_execution_flow


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

    @mock.patch("src.pressreader.NOTIFY")
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

    @mock.patch("src.pressreader.NOTIFY")
    @mock.patch("src.pressreader.chromium")
    @mock.patch("src.pressreader.Page.locator")
    def test_access_information_retrieved_correctly(
        self, page_html_mock, clean_mock, global_notifier_mock
    ):
        global_notifier_mock.disabled = False
        clean_mock.clean.return_value = "mocking clean call"
        page_html_mock.return_value.inner_text.return_value = (
            "Complimentary access: 6 days"
        )

        mocked_resource_url = "https://www.example.com/catalog"

        self.chromium.visit_site(page=self.page, url=mocked_resource_url)

        assert verify_execution_flow(self.page)[0] is True

    @mock.patch("src.pressreader.NOTIFY")
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
