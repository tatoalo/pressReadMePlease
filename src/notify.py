from pathlib import Path
import requests
import logging

REQUEST_TIMEOUT_SECONDS = 30


class Notifier:
    def __init__(
        self,
        url: str = None,
        token: str = None,
        chat_id: str = None,
    ):
        if url is not None and token is not None and chat_id is not None:
            self.api_url = url + token
            self.disabled = False
        else:
            self.api_url = ""
            self.disabled = True
        self.chat_id = chat_id
        self.screenshot_client = None
        self._token = token

    def set_screenshot_client(self, client):
        self.screenshot_client = client

    def send_message(self, message: str):
        if self.disabled is False:
            payload = {"chat_id": self.chat_id, "text": message}
            self._post("sendMessage", data=payload)

    def send_image(self, image_location: Path):
        if self.disabled is False and self.screenshot_client:
            self._post_file("sendPhoto", "photo", image_location)
        elif not self.screenshot_client and not self.disabled:
            logging.warning(
                "Notifier.send_image called but screenshot_client is not set."
            )

    def send_binary(self, binary_path: Path):
        if self.disabled is False:
            self._post_file("sendDocument", "document", binary_path)

    def _post_file(self, method: str, field: str, path: Path):
        with open(path, "rb") as file:
            self._post(method, data={"chat_id": self.chat_id}, files=[(field, file)])

    def _post(self, method: str, **kwargs):
        try:
            requests.post(
                self.api_url + method, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs
            )
        except requests.RequestException as e:
            logging.error(f"Telegram {method} request failed: {self._redact(str(e))}")

    def _redact(self, text: str) -> str:
        if self._token:
            return text.replace(self._token, "<redacted>")
        return text
