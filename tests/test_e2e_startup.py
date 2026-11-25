import io
from contextlib import redirect_stdout
from unittest import TestCase, mock

import requests

from src import e2e_startup
from src.e2e_startup import get_latest_version_from_github, parse_version


def tags_response(*names, status_code=200):
    response = mock.Mock()
    response.status_code = status_code
    response.json.return_value = [{"name": name} for name in names]
    return response


class TestParseVersion(TestCase):
    def test_parses_plain_and_prefixed_versions(self):
        self.assertEqual(parse_version("3.3.1"), (3, 3, 1))
        self.assertEqual(parse_version("v3.3.1"), (3, 3, 1))
        self.assertEqual(parse_version("v3.10.0"), (3, 10, 0))
        self.assertEqual(parse_version(" 3.2 "), (3, 2))

    def test_returns_none_for_unparseable_versions(self):
        for value in (
            "",
            "v",
            "latest",
            "3.3.1-rc1",
            "3..1",
            "3.3.",
            "v3.x.0",
            "3.²",
            None,
        ):
            with self.subTest(value=value):
                self.assertIsNone(parse_version(value))

    def test_compares_numerically(self):
        self.assertGreater(parse_version("3.10.0"), parse_version("3.9.0"))
        self.assertGreater(parse_version("v3.3.10"), parse_version("3.3.9"))
        self.assertLess("3.10.0", "3.9.0")


class TestGetLatestVersionFromGithub(TestCase):
    @mock.patch("src.e2e_startup.requests.get")
    def test_picks_highest_tag_from_unordered_list(self, get_mock):
        get_mock.return_value = tags_response(
            "v3.9.0", "nightly", "v3.10.0", "v3.2.11", "3.10.0-beta", "v3.1.15"
        )

        self.assertEqual(get_latest_version_from_github(), "3.10.0")
        self.assertEqual(get_mock.call_args.kwargs["timeout"], 10)

    @mock.patch("src.e2e_startup.requests.get")
    def test_returns_none_when_no_tag_is_parseable(self, get_mock):
        get_mock.return_value = tags_response("nightly", "latest")

        self.assertIsNone(get_latest_version_from_github())

    @mock.patch("src.e2e_startup.requests.get")
    def test_returns_none_on_non_200_status(self, get_mock):
        get_mock.return_value = tags_response("v3.3.1", status_code=403)

        self.assertIsNone(get_latest_version_from_github())

    @mock.patch("src.e2e_startup.requests.get")
    def test_network_failure_is_non_fatal(self, get_mock):
        get_mock.side_effect = requests.ConnectionError("network down")
        output = io.StringIO()

        with redirect_stdout(output):
            result = get_latest_version_from_github()

        self.assertIsNone(result)
        self.assertIn("Could not fetch latest version from GitHub", output.getvalue())


class TestMain(TestCase):
    def run_main(self, current_version, tags=None, get_side_effect=None):
        output = io.StringIO()
        with (
            mock.patch.object(
                e2e_startup, "get_current_version", return_value=current_version
            ),
            mock.patch.object(
                e2e_startup, "run_basic_sanity_checks", return_value=True
            ),
            mock.patch("src.e2e_startup.requests.get") as get_mock,
            redirect_stdout(output),
        ):
            if get_side_effect is not None:
                get_mock.side_effect = get_side_effect
            else:
                get_mock.return_value = tags_response(*tags)
            exit_code = e2e_startup.main()
        return exit_code, output.getvalue()

    def test_current_3_10_is_newer_than_latest_3_9(self):
        exit_code, output = self.run_main("3.10.0", tags=["v3.9.0", "v3.8.2"])

        self.assertEqual(exit_code, 0)
        self.assertIn("📋 Latest available version: 3.9.0", output)
        self.assertIn("You are running a newer version than the latest release", output)

    def test_latest_3_10_is_newer_than_current_3_9(self):
        exit_code, output = self.run_main("3.9.0", tags=["v3.9.0", "v3.10.0"])

        self.assertEqual(exit_code, 0)
        self.assertIn("⚠️  A newer version is available: 3.10.0", output)

    def test_running_latest_version(self):
        exit_code, output = self.run_main("3.3.1", tags=["v3.3.0", "v3.3.1"])

        self.assertEqual(exit_code, 0)
        self.assertIn("✓ You are running the latest version!", output)

    def test_unparseable_current_version_does_not_crash(self):
        exit_code, output = self.run_main("3.4.0rc1", tags=["v3.3.1"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Could not compare unparseable version 3.4.0rc1", output)

    def test_github_failure_is_non_fatal(self):
        exit_code, output = self.run_main(
            "3.3.1", get_side_effect=requests.Timeout("timed out")
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Could not fetch latest version from GitHub", output)
        self.assertIn("Could not determine latest version from GitHub", output)
        self.assertIn("E2E startup test completed successfully!", output)
