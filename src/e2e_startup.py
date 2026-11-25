#!/usr/bin/env python3
"""
E2E startup test script that validates the application and checks version information.
"""

import re
import sys
from importlib.util import find_spec
from pathlib import Path

import requests
import tomlkit

PROJECT_ROOT = Path(__file__).parent.parent

VERSION_PATTERN = re.compile(r"v?([0-9]+(?:\.[0-9]+)*)")


def parse_version(version: str) -> tuple[int, ...] | None:
    if not isinstance(version, str):
        return None
    match = VERSION_PATTERN.fullmatch(version.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def get_current_version() -> str:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        data = tomlkit.load(f)
    return data["project"]["version"]


def get_latest_version_from_github() -> str | None:
    try:
        url = "https://api.github.com/repos/tatoalo/pressReadMePlease/tags"
        response = requests.get(url, params={"per_page": 100}, timeout=10)
        if response.status_code == 200:
            versions = [parse_version(tag.get("name")) for tag in response.json()]
            versions = [version for version in versions if version is not None]
            if versions:
                return ".".join(str(part) for part in max(versions))

        return None
    except Exception as e:
        print(f"⚠️  Could not fetch latest version from GitHub: {e}")
        return None


def run_basic_sanity_checks() -> bool:
    try:
        # Check that required dependencies are available
        if find_spec("playwright") is None:
            print("✗ Playwright module not found")
            return False
        print("✓ Playwright module available")

        if find_spec("tomlkit") is None:
            print("✗ Tomlkit module not found")
            return False
        print("✓ Tomlkit module available")

        src_path = PROJECT_ROOT / "src"
        if src_path.exists() and src_path.is_dir():
            print("✓ Source directory found")

            main_script = src_path / "pressreadmeplease.py"
            if main_script.exists():
                print("✓ Main script found")
            else:
                print("⚠️  Main script not found")
        else:
            print("✗ Source directory not found")
            return False

        config_path = src_path / "config.toml"
        if config_path.exists():
            print("✓ Configuration file found")
        else:
            print("⚠️  Configuration file not found (expected in production)")

        # Test that the main script and its dependencies can be imported
        print("✓ Testing module imports...")
        # This mimics the PYTHONPATH="/" setup in the container
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        try:
            # Try to import the main modules that pressreadmeplease.py depends on
            import chromium  # noqa: F401

            print("  ✓ chromium module can be imported")

            import mlol  # noqa: F401

            print("  ✓ mlol module can be imported")

            import pressreader  # noqa: F401

            print("  ✓ pressreader module can be imported")

            import utilities  # noqa: F401

            print("  ✓ utilities module can be imported")

            import configuration  # noqa: F401

            print("  ✓ configuration module can be imported")

            print("✓ All required modules can be imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import required module: {e}")
            print("  This would cause the cron job to fail!")
            return False

        return True
    except ImportError as e:
        print(f"✗ Missing required dependency: {e}")
        return False
    except Exception as e:
        print(f"✗ Sanity check failed: {e}")
        return False


def main() -> int:
    """Main e2e startup test function."""
    print("=" * 70)
    print("🚀 PressReadMePlease E2E Startup Test")
    print("=" * 70)

    try:
        current_version = get_current_version()
        print(f"\n📦 You are running version {current_version}")
    except Exception as e:
        print(f"✗ Failed to read current version: {e}")
        return 1

    print("\n🔍 Checking for latest version on GitHub...")
    latest_version = get_latest_version_from_github()

    if latest_version:
        print(f"📋 Latest available version: {latest_version}")

        current = parse_version(current_version)
        latest = parse_version(latest_version)
        if current is None:
            print(f"⚠️  Could not compare unparseable version {current_version}")
        elif current == latest:
            print("✓ You are running the latest version!")
        elif current > latest:
            print("ℹ️  You are running a newer version than the latest release")
        else:
            print(f"⚠️  A newer version is available: {latest_version}")
    else:
        print("⚠️  Could not determine latest version from GitHub")

    print("\n🧪 Running sanity checks...")
    if not run_basic_sanity_checks():
        print("\n✗ E2E startup test failed!")
        return 1

    print("\n" + "=" * 70)
    print("✓ E2E startup test completed successfully!")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
