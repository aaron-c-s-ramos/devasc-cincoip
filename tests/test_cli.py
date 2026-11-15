"""Tests of cincoip/cli.py.

These tests run the full application with prepared API replies. They send
no network requests.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from cincoip import cli
from cincoip.api_client import ApiError

GEO_DATA = {
    "city": "Manila",
    "region": "Metro Manila",
    "country": "Philippines",
    "country_code": "PH",
    "latitude": 14.5995,
    "longitude": 120.9842,
    "timezone": "Asia/Manila",
    "utc_offset": "+08:00",
    "isp": "Example ISP",
    "org": "Example Org",
    "asn": "AS64500",
    "source": "ipwho.is",
}


def fake_fetch(version):
    """Give an IPv4 address, and no IPv6 address."""
    if version == 4:
        return {"version": 4, "address": "203.0.113.7", "error": None}
    return {
        "version": 6,
        "address": None,
        "error": "IPv6 is not available on this network (test)",
    }


def run(arguments):
    """Run the application and return (exit code, output, error output)."""
    output = io.StringIO()
    errors = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        code = cli.main(arguments)
    return code, output.getvalue(), errors.getvalue()


@mock.patch("cincoip.cli.geo.lookup", return_value=dict(GEO_DATA))
@mock.patch("cincoip.cli.api_client.fetch_public_ip", side_effect=fake_fetch)
class OwnAddressTests(unittest.TestCase):
    # 203.0.113.7 is a documentation address. Python gives it the category
    # "private", thus these tests replace classify_ip where the location
    # data is necessary.

    def test_default_run_shows_the_two_versions(self, fake_ip, fake_geo):
        with mock.patch("cincoip.cli.validators.classify_ip", return_value="public"):
            code, output, _ = run([])
        self.assertEqual(code, 0)
        self.assertIn("Public IPv4", output)
        self.assertIn("203.0.113.7", output)
        self.assertIn("Philippines (PH)", output)
        self.assertIn("Public IPv6", output)
        self.assertIn("IPv6 is not available", output)
        self.assertEqual([call[0][0] for call in fake_ip.call_args_list], [4, 6])

    def test_ipv4_only(self, fake_ip, fake_geo):
        code, output, _ = run(["-4"])
        self.assertEqual(code, 0)
        self.assertNotIn("Public IPv6", output)
        self.assertEqual([call[0][0] for call in fake_ip.call_args_list], [4])

    def test_ipv6_only_without_ipv6_gives_exit_code_1(self, fake_ip, fake_geo):
        code, output, _ = run(["-6"])
        self.assertEqual(code, 1)
        self.assertNotIn("Public IPv4", output)

    def test_no_geo_sends_no_location_request(self, fake_ip, fake_geo):
        with mock.patch("cincoip.cli.validators.classify_ip", return_value="public"):
            code, output, _ = run(["--no-geo"])
        self.assertEqual(code, 0)
        fake_geo.assert_not_called()
        self.assertNotIn("Country", output)

    def test_json_output_is_valid(self, fake_ip, fake_geo):
        with mock.patch("cincoip.cli.validators.classify_ip", return_value="public"):
            code, output, _ = run(["--json"])
        report = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(report["results"][0]["address"], "203.0.113.7")
        self.assertEqual(report["results"][0]["geo"]["country_code"], "PH")
        self.assertIsNone(report["results"][1]["address"])

    def test_location_failure_does_not_stop_the_report(self, fake_ip, fake_geo):
        fake_geo.side_effect = ApiError("ipwho.is: HTTP status 429")
        with mock.patch("cincoip.cli.validators.classify_ip", return_value="public"):
            code, output, _ = run(["-4"])
        self.assertEqual(code, 0)
        self.assertIn("203.0.113.7", output)
        self.assertIn("Location data", output)
        self.assertIn("429", output)

    def test_save_writes_the_file(self, fake_ip, fake_geo):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "report.json")
            code, output, errors = run(["--json", "--save", path])
            self.assertEqual(code, 0)
            self.assertIn("Report saved", errors)
            # The JSON on the standard output must stay valid.
            json.loads(output)
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(len(json.load(handle)["results"]), 2)
        finally:
            shutil.rmtree(folder)

    def test_save_failure_gives_exit_code_1(self, fake_ip, fake_geo):
        code, _, errors = run(
            ["--save", os.path.join("folder-that-does-not-exist", "r.txt")]
        )
        self.assertEqual(code, 1)
        self.assertIn("The report was not saved", errors)


@mock.patch("cincoip.cli.geo.lookup", return_value=dict(GEO_DATA))
@mock.patch("cincoip.cli.api_client.fetch_public_ip", side_effect=fake_fetch)
class GivenAddressTests(unittest.TestCase):
    def test_public_address_gets_location_data(self, fake_ip, fake_geo):
        code, output, _ = run(["--ip", "8.8.8.8"])
        self.assertEqual(code, 0)
        self.assertIn("Lookup: 8.8.8.8", output)
        self.assertIn("Manila", output)
        fake_ip.assert_not_called()
        fake_geo.assert_called_once_with("8.8.8.8")

    def test_private_address_is_not_sent_to_the_api(self, fake_ip, fake_geo):
        code, output, _ = run(["--ip", "192.168.1.10"])
        self.assertEqual(code, 0)
        self.assertIn("Private", output)
        self.assertIn("Not available for an address of the type", output)
        fake_geo.assert_not_called()

    def test_text_that_is_not_an_address(self, fake_ip, fake_geo):
        code, output, _ = run(["--ip", "999.1.1.1"])
        self.assertEqual(code, 1)
        self.assertIn("not a valid IPv4 or IPv6 address", output)
        fake_geo.assert_not_called()

    def test_more_than_one_address(self, fake_ip, fake_geo):
        code, output, _ = run(["--ip", "8.8.8.8", "--ip", "2001:4860:4860::8888"])
        self.assertEqual(code, 0)
        self.assertIn("Lookup: 8.8.8.8", output)
        self.assertIn("Lookup: 2001:4860:4860::8888", output)
        self.assertEqual(fake_geo.call_count, 2)


class OptionTests(unittest.TestCase):
    def test_ipv4_and_ipv6_options_together_are_rejected(self):
        with self.assertRaises(SystemExit) as context:
            run(["-4", "-6"])
        self.assertEqual(context.exception.code, 2)

    def test_version_option(self):
        with self.assertRaises(SystemExit) as context:
            run(["--version"])
        self.assertEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
