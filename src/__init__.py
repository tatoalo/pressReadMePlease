from pathlib import Path
from utilities import load_configuration, load_notifier

# ms
TIMEOUT = 30000

CORRECT_FLOW_DAYS_RESET = 6

PROJECT_ROOT = Path(__file__).parent

CONFIGURATION = load_configuration(path=PROJECT_ROOT / "config.toml")

NOTIFIER = load_notifier(configuration=CONFIGURATION, project_root=PROJECT_ROOT)
