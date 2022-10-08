from notify import Notifier
def load_notifier(*, configuration: Configuration, project_root: Path) -> Notifier:
    telegram_base_url = configuration.telegram_base_url
    telegram_token = configuration.telegram_token
    telegram_chat_id = configuration.telegram_chat_id

    n = Notifier(url=telegram_base_url, token=telegram_token, chat_id=telegram_chat_id)

    if None not in (telegram_base_url, telegram_token, telegram_chat_id):
        n.screenshot_client = Screenshot(n, path=project_root)

    return n
