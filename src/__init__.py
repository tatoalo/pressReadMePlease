import logging
from pathlib import Path

from utilities import load_configuration, load_notifier

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)

# ms
TIMEOUT = 30000

CORRECT_FLOW_DAYS_RESET = 2

WARNING_FAILED_LOGIN_TEXT_ELEMENT = "avviso"

PROJECT_ROOT = Path(__file__).parent

CONFIGURATION_FILE = "config.toml"

RUNNING_LOG_FILE = PROJECT_ROOT / "running_log.txt"

CONFIGURATION = load_configuration(path=PROJECT_ROOT / CONFIGURATION_FILE)

NOTIFIER = load_notifier(configuration=CONFIGURATION, project_root=PROJECT_ROOT)
