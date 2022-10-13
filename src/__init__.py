from pathlib import Path
from utilities import load_configuration, load_notifier

# ms
TIMEOUT = 30000

CORRECT_FLOW_DAYS_RESET = 6

PROJECT_ROOT = Path(__file__).parent

CONFIGURATION_FILE = "config.toml"

CONFIGURATION = load_configuration(path=PROJECT_ROOT / CONFIGURATION_FILE)

NOTIFIER = load_notifier(configuration=CONFIGURATION, project_root=PROJECT_ROOT)
