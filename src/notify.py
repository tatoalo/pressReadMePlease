import requests


class Notifier:
    def __init__(self, url=None, token=None, chat_id=None, screenshot_client=None):
        if url is not None and token is not None:
            self.api_url = url+token
            self.disabled = False
        else:
            self.api_url = ""
            self.disabled = True
        self.chat_id = chat_id
        self.screenshot_client = screenshot_client

    def send_message(self, message):
        if self.disabled is False:
            payload = {'chat_id': self.chat_id, 'text': message}
            requests.post(self.api_url + 'sendMessage', data=payload)

    def send_image(self, image_location):
        if self.disabled is False:
            payload = {'chat_id': self.chat_id}
            files = [
                ('photo', open(image_location, 'rb'))
            ]
            headers = {}
            requests.post(self.api_url + 'sendPhoto', data=payload, files=files)