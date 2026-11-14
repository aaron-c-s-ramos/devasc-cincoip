"""Tests of cincoip/formatter.py."""

import io
import json
import os
import unittest
from unittest import mock

from cincoip import formatter

FULL_RECORD = {
    "label": "Public IPv4",
    "address": "8.8.8.8",
    "version": 4,
    "category": "public",
    "error": None,
    "geo": {
        "city": "San Jose",
        "region": "California",
        "country": "United States",
        "country_code": "US",
        "latitude": 37.3393939,
        "longitude": -121.8949553,
        "timezone": "America/Los_Angeles",
        "utc_offset": "-08:00",
        "isp": "Google LLC",
        "org": "Google LLC",
        "asn": "AS15169",
        "source": "ipwho.is",
    },
    "geo_error": None,
}

NO_ADDRESS_RECORD = {
    "label": "Public IPv6",
    "address": None,
    "version": 6,
    "category": None,
    "error": "IPv6 is not available on this network (connection failed)",
    "geo": None,
    "geo_error": None,
}


class RecordRowsTests(unittest.TestCase):
    def test_full_record_has_all_rows(self):
        rows = dict(
            (name, value) for name, value, _ in formatter.record_rows(FULL_RECORD)
        )
        self.assertEqual(rows["Address"], "8.8.8.8")
        self.assertEqual(rows["IP version"], "IPv4")
        self.assertEqual(rows["Address type"], "Public")
        self.assertEqual(rows["Country"], "United States (US)")
        self.assertEqual(rows["Coordinates"], "37.3393939, -121.8949553")
        self.assertEqual(rows["Time zone"], "America/Los_Angeles (UTC -08:00)")
        self.assertEqual(rows["ASN"], "AS15169")
        self.assertEqual(rows["Data source"], "ipwho.is")

    def test_record_without_address_shows_only_the_status(self):
        rows = formatter.record_rows(NO_ADDRESS_RECORD)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Status")
        self.assertIn("IPv6 is not available", rows[0][1])

    def test_location_failure_shows_one_row(self):
        record = dict(FULL_RECORD, geo=None, geo_error="Not available (x)")
        names = [name for name, _, _ in formatter.record_rows(record)]
        self.assertEqual(
            names, ["Address", "IP version", "Address type", "Location data"]
        )

    def test_empty_values_show_a_dash(self):
        geo = dict(FULL_RECORD["geo"], city=None, latitude=None)
        record = dict(FULL_RECORD, geo=geo)
        rows = dict(
            (name, value) for name, value, _ in formatter.record_rows(record)
        )
        self.assertEqual(rows["City"], "-")
        self.assertEqual(rows["Coordinates"], "-")


class FormatTextTests(unittest.TestCase):
    def test_all_lines_of_a_table_have_the_same_width(self):
        for record in (FULL_RECORD, NO_ADDRESS_RECORD):
            lines = formatter.format_record(record).splitlines()
            widths = set(len(line) for line in lines)
            self.assertEqual(len(widths), 1, lines)

    def test_long_value_is_divided_into_lines(self):
        lines = formatter.format_record(NO_ADDRESS_RECORD).splitlines()
        for line in lines:
            self.assertLessEqual(len(line), 80, line)
        text = " ".join(line.strip("| ") for line in lines)
        self.assertIn("IPv6 is not available on this network", text)

    def test_long_title_makes_the_table_wider(self):
        record = dict(NO_ADDRESS_RECORD, label="Lookup: " + "x" * 90, error="e")
        lines = formatter.format_record(record).splitlines()
        self.assertEqual(len(set(len(line) for line in lines)), 1)

    def test_text_without_color_has_no_escape_codes(self):
        text = formatter.format_text([FULL_RECORD], "2026-11-12 10:00:00")
        self.assertNotIn("\033", text)
        self.assertIn("Public IPv4", text)
        self.assertIn("Generated: 2026-11-12 10:00:00", text)

    def test_text_with_color_has_escape_codes(self):
        text = formatter.format_text([FULL_RECORD], use_color=True)
        self.assertIn(formatter.GREEN, text)
        self.assertIn(formatter.RESET, text)

    def test_color_does_not_change_the_text(self):
        plain = formatter.format_text([FULL_RECORD, NO_ADDRESS_RECORD])
        colored = formatter.format_text(
            [FULL_RECORD, NO_ADDRESS_RECORD], use_color=True
        )
        for code in (formatter.RESET, formatter.BOLD, formatter.RED,
                     formatter.GREEN, formatter.YELLOW, formatter.CYAN):
            colored = colored.replace(code, "")
        self.assertEqual(plain, colored)

    def test_output_contains_only_ascii_for_ascii_data(self):
        text = formatter.format_text([FULL_RECORD, NO_ADDRESS_RECORD])
        text.encode("ascii")


class FormatJsonTests(unittest.TestCase):
    def test_json_is_valid_and_complete(self):
        text = formatter.format_json(
            [FULL_RECORD, NO_ADDRESS_RECORD], "2026-11-12 10:00:00"
        )
        report = json.loads(text)
        self.assertEqual(report["application"], "CincoIP")
        self.assertEqual(report["generated"], "2026-11-12 10:00:00")
        self.assertEqual(len(report["results"]), 2)
        self.assertEqual(report["results"][0]["geo"]["asn"], "AS15169")
        self.assertIsNone(report["results"][1]["address"])


class SupportsColorTests(unittest.TestCase):
    def test_stream_that_is_not_a_terminal(self):
        self.assertFalse(formatter.supports_color(io.StringIO()))

    def test_no_color_variable_stops_the_colors(self):
        stream = mock.Mock()
        stream.isatty.return_value = True
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(formatter.supports_color(stream))

    def test_terminal_gets_colors(self):
        stream = mock.Mock()
        stream.isatty.return_value = True
        environment = dict(os.environ)
        environment.pop("NO_COLOR", None)
        with mock.patch.dict(os.environ, environment, clear=True):
            with mock.patch("cincoip.formatter.os.system"):
                self.assertTrue(formatter.supports_color(stream))


if __name__ == "__main__":
    unittest.main()
