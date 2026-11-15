"""Tests of cincoip/exporter.py. The tests write files to a temporary folder."""

import csv
import json
import os
import shutil
import tempfile
import unittest

from cincoip import exporter
from tests.test_formatter import FULL_RECORD, NO_ADDRESS_RECORD

RECORDS = [FULL_RECORD, NO_ADDRESS_RECORD]


class DetectFormatTests(unittest.TestCase):
    def test_extension_sets_the_format(self):
        self.assertEqual(exporter.detect_format("report.json"), "json")
        self.assertEqual(exporter.detect_format("REPORT.CSV"), "csv")
        self.assertEqual(exporter.detect_format("report.txt"), "text")
        self.assertEqual(exporter.detect_format("report"), "text")


class SaveReportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder)

    def path(self, name):
        return os.path.join(self.folder, name)

    def test_text_file_contains_the_table_without_colors(self):
        kind = exporter.save_report(RECORDS, self.path("r.txt"), "2026-11-12")
        self.assertEqual(kind, "text")
        with open(self.path("r.txt"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("8.8.8.8", text)
        self.assertIn("Public IPv6", text)
        self.assertNotIn("\033", text)

    def test_json_file_is_valid(self):
        kind = exporter.save_report(RECORDS, self.path("r.json"), "2026-11-12")
        self.assertEqual(kind, "json")
        with open(self.path("r.json"), encoding="utf-8") as handle:
            report = json.load(handle)
        self.assertEqual(len(report["results"]), 2)

    def test_csv_file_has_one_row_for_each_record(self):
        kind = exporter.save_report(RECORDS, self.path("r.csv"))
        self.assertEqual(kind, "csv")
        with open(self.path("r.csv"), encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["address"], "8.8.8.8")
        self.assertEqual(rows[0]["asn"], "AS15169")
        self.assertEqual(rows[0]["source"], "ipwho.is")
        self.assertEqual(rows[1]["address"], "")
        self.assertIn("IPv6 is not available", rows[1]["error"])

    def test_folder_that_does_not_exist_raises_os_error(self):
        with self.assertRaises(OSError):
            exporter.save_report(
                RECORDS, os.path.join(self.folder, "missing", "r.txt")
            )


if __name__ == "__main__":
    unittest.main()
