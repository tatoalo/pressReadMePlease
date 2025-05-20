from pathlib import Path
import requests
import logging


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

    def set_screenshot_client(self, client):
        self.screenshot_client = client

    def send_message(self, message: str):
        if self.disabled is False:
            payload = {"chat_id": self.chat_id, "text": message}
            requests.post(self.api_url + "sendMessage", data=payload)

    def send_image(self, image_location: Path):
        if self.disabled is False and self.screenshot_client:
            payload = {"chat_id": self.chat_id}
            files = [("photo", open(image_location, "rb"))]
            requests.post(self.api_url + "sendPhoto", data=payload, files=files)
        elif not self.screenshot_client and not self.disabled:
            logging.warning(
                "Notifier.send_image called but screenshot_client is not set."
            )
            pass

    def send_binary(self, binary_path: Path):
        if self.disabled is False:
            payload = {"chat_id": self.chat_id}
            files = [("document", open(binary_path, "rb"))]
            requests.post(self.api_url + "sendDocument", data=payload, files=files)
