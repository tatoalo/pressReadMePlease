import tempfile
from pathlib import Path
from unittest import TestCase, mock

import requests

from src.notify import REQUEST_TIMEOUT_SECONDS, Notifier

BASE_URL = "https://api.telegram.org/bot"
TOKEN = "123456:secret-token/"
CHAT_ID = "6942"


class TestNotifier(TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.file_path = Path(self.tmp_dir.name) / "attachment.png"
        self.file_path.write_bytes(b"content")

        self.notifier = Notifier(url=BASE_URL, token=TOKEN, chat_id=CHAT_ID)
        self.notifier.set_screenshot_client(mock.Mock())

    def _send_all(self, notifier: Notifier) -> None:
        notifier.send_message("hello")
        notifier.send_image(image_location=self.file_path)
        notifier.send_binary(binary_path=self.file_path)

    @mock.patch("src.notify.requests.post")
    def test_disabled_notifier_sends_nothing(self, post_mock):
        for notifier in (
            Notifier(),
            Notifier(url=BASE_URL, token=TOKEN),
            Notifier(url=BASE_URL, chat_id=CHAT_ID),
            Notifier(token=TOKEN, chat_id=CHAT_ID),
        ):
            with self.subTest(api_url=notifier.api_url, chat_id=notifier.chat_id):
                self.assertTrue(notifier.disabled)
                notifier.set_screenshot_client(mock.Mock())
                self._send_all(notifier)

        post_mock.assert_not_called()

    def test_enabled_notifier_builds_api_url(self):
        self.assertFalse(self.notifier.disabled)
        self.assertEqual(self.notifier.api_url, BASE_URL + TOKEN)

    @mock.patch("src.notify.requests.post")
    def test_send_message_passes_timeout(self, post_mock):
        self.notifier.send_message("hello")

        post_mock.assert_called_once_with(
            BASE_URL + TOKEN + "sendMessage",
            data={"chat_id": CHAT_ID, "text": "hello"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    @mock.patch("src.notify.requests.post")
    def test_send_image_passes_timeout(self, post_mock):
        self.notifier.send_image(image_location=self.file_path)

        post_mock.assert_called_once()
        args, kwargs = post_mock.call_args
        self.assertEqual(args, (BASE_URL + TOKEN + "sendPhoto",))
        self.assertEqual(kwargs["timeout"], REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(kwargs["data"], {"chat_id": CHAT_ID})
        self.assertEqual(kwargs["files"][0][0], "photo")

    @mock.patch("src.notify.requests.post")
    def test_send_binary_passes_timeout(self, post_mock):
        self.notifier.send_binary(binary_path=self.file_path)

        post_mock.assert_called_once()
        args, kwargs = post_mock.call_args
        self.assertEqual(args, (BASE_URL + TOKEN + "sendDocument",))
        self.assertEqual(kwargs["timeout"], REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(kwargs["data"], {"chat_id": CHAT_ID})
        self.assertEqual(kwargs["files"][0][0], "document")

    def test_timeout_is_thirty_seconds(self):
        self.assertEqual(REQUEST_TIMEOUT_SECONDS, 30)

    @mock.patch("src.notify.requests.post")
    def test_send_image_without_screenshot_client_warns(self, post_mock):
        notifier = Notifier(url=BASE_URL, token=TOKEN, chat_id=CHAT_ID)

        with self.assertLogs(level="WARNING") as logs:
            notifier.send_image(image_location=self.file_path)

        post_mock.assert_not_called()
        self.assertIn("screenshot_client is not set", "\n".join(logs.output))

    @mock.patch("src.notify.requests.post")
    def test_request_exception_is_swallowed_and_logged(self, post_mock):
        sends = {
            "sendMessage": lambda: self.notifier.send_message("hello"),
            "sendPhoto": lambda: self.notifier.send_image(
                image_location=self.file_path
            ),
            "sendDocument": lambda: self.notifier.send_binary(
                binary_path=self.file_path
            ),
        }
        errors = (
            (
                requests.ConnectionError(
                    f"Max retries exceeded with url: /bot{TOKEN}sendMessage"
                ),
                "Max retries exceeded",
            ),
            (requests.Timeout("Read timed out."), "Read timed out."),
        )

        for method, send in sends.items():
            for error, expected in errors:
                with self.subTest(method=method, error=type(error).__name__):
                    post_mock.reset_mock()
                    post_mock.side_effect = error

                    with self.assertLogs(level="ERROR") as logs:
                        send()

                    post_mock.assert_called_once()
                    output = "\n".join(logs.output)
                    self.assertIn(method, output)
                    self.assertIn(expected, output)
                    self.assertNotIn(TOKEN, output)

    @mock.patch("src.notify.requests.post")
    def test_file_handles_are_closed(self, post_mock):
        sends = {
            "send_image": lambda: self.notifier.send_image(
                image_location=self.file_path
            ),
            "send_binary": lambda: self.notifier.send_binary(
                binary_path=self.file_path
            ),
        }

        for name, send in sends.items():
            for error in (None, requests.ConnectionError("boom")):
                with self.subTest(method=name, failing=error is not None):
                    handles = []

                    def capture(*args, **kwargs):
                        handle = kwargs["files"][0][1]
                        handles.append((handle, handle.closed))
                        if error is not None:
                            raise error

                    post_mock.reset_mock()
                    post_mock.side_effect = capture

                    send()

                    self.assertEqual(len(handles), 1)
                    handle, closed_during_send = handles[0]
                    self.assertFalse(closed_during_send)
                    self.assertTrue(handle.closed)
