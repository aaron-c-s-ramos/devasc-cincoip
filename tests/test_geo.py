"""Tests of cincoip/geo.py.

These tests send no network requests. The sample replies below have the
same key names as the real replies of each API.
"""

import unittest
from unittest import mock

from cincoip import geo
from cincoip.api_client import ApiError

# A reply of https://ipwho.is/8.8.8.8 (short form).
IPWHOIS_REPLY = {
    "ip": "8.8.8.8",
    "success": True,
    "type": "IPv4",
    "country": "United States",
    "country_code": "US",
    "region": "California",
    "city": "San Jose",
    "latitude": 37.3393939,
    "longitude": -121.8949553,
    "connection": {
        "asn": 15169,
        "org": "Google LLC",
        "isp": "Google LLC",
        "domain": "google.com",
    },
    "timezone": {"id": "America/Los_Angeles", "utc": "-08:00"},
}

# A reply of https://ipapi.co/8.8.8.8/json/ (short form).
IPAPI_REPLY = {
    "ip": "8.8.8.8",
    "city": "Mountain View",
    "region": "California",
    "country_name": "United States",
    "country_code": "US",
    "latitude": 37.42301,
    "longitude": -122.083352,
    "timezone": "America/Los_Angeles",
    "utc_offset": "-0800",
    "asn": "AS15169",
    "org": "GOOGLE",
}


class FormatAsnTests(unittest.TestCase):
    def test_number_gets_the_prefix(self):
        self.assertEqual(geo.format_asn(15169), "AS15169")

    def test_text_with_prefix_stays_the_same(self):
        self.assertEqual(geo.format_asn("AS15169"), "AS15169")
        self.assertEqual(geo.format_asn("as15169"), "AS15169")

    def test_no_value(self):
        self.assertIsNone(geo.format_asn(None))
        self.assertIsNone(geo.format_asn(""))


class LookupTests(unittest.TestCase):
    @mock.patch("cincoip.geo.get_json")
    def test_first_provider_gives_the_data(self, fake_get_json):
        fake_get_json.return_value = IPWHOIS_REPLY
        record = geo.lookup("8.8.8.8")
        self.assertEqual(record["source"], "ipwho.is")
        self.assertEqual(record["city"], "San Jose")
        self.assertEqual(record["country_code"], "US")
        self.assertEqual(record["isp"], "Google LLC")
        self.assertEqual(record["asn"], "AS15169")
        self.assertEqual(record["timezone"], "America/Los_Angeles")
        self.assertEqual(fake_get_json.call_count, 1)

    @mock.patch("cincoip.geo.get_json")
    def test_result_has_all_the_standard_keys(self, fake_get_json):
        fake_get_json.return_value = IPWHOIS_REPLY
        record = geo.lookup("8.8.8.8")
        for key in geo.GEO_KEYS + ("source",):
            self.assertIn(key, record)

    @mock.patch("cincoip.geo.get_json")
    def test_second_provider_is_used_when_the_first_fails(self, fake_get_json):
        fake_get_json.side_effect = [ApiError("HTTP status 429"), IPAPI_REPLY]
        record = geo.lookup("8.8.8.8")
        self.assertEqual(record["source"], "ipapi.co")
        self.assertEqual(record["country"], "United States")
        self.assertEqual(record["asn"], "AS15169")
        self.assertEqual(record["isp"], "GOOGLE")
        self.assertEqual(
            fake_get_json.call_args[0][0], "https://ipapi.co/8.8.8.8/json/"
        )

    @mock.patch("cincoip.geo.get_json")
    def test_error_in_a_status_200_reply_starts_the_fallback(
        self, fake_get_json
    ):
        fake_get_json.side_effect = [
            {"ip": "8.8.8.8", "success": False, "message": "Rate limit exceeded"},
            IPAPI_REPLY,
        ]
        self.assertEqual(geo.lookup("8.8.8.8")["source"], "ipapi.co")

    @mock.patch("cincoip.geo.get_json")
    def test_all_providers_fail(self, fake_get_json):
        fake_get_json.side_effect = [
            ApiError("the connection to the server failed"),
            {"error": True, "reason": "RateLimited"},
        ]
        with self.assertRaises(ApiError) as context:
            geo.lookup("8.8.8.8")
        message = str(context.exception)
        self.assertIn("ipwho.is", message)
        self.assertIn("ipapi.co", message)
        self.assertIn("RateLimited", message)

    @mock.patch("cincoip.geo.get_json")
    def test_ipv6_address_goes_into_the_url(self, fake_get_json):
        fake_get_json.return_value = IPWHOIS_REPLY
        geo.lookup("2001:4860:4860:0:0:0:0:8888")
        self.assertEqual(
            fake_get_json.call_args[0][0],
            "https://ipwho.is/2001:4860:4860::8888",
        )

    @mock.patch("cincoip.geo.get_json")
    def test_text_that_is_not_an_address_sends_no_request(self, fake_get_json):
        with self.assertRaises(ValueError):
            geo.lookup("8.8.8.8/../admin")
        fake_get_json.assert_not_called()

    @mock.patch("cincoip.geo.get_json")
    def test_keys_that_are_not_in_the_reply_become_none(self, fake_get_json):
        fake_get_json.return_value = {"success": True, "country": "Philippines"}
        record = geo.lookup("8.8.8.8")
        self.assertEqual(record["country"], "Philippines")
        self.assertIsNone(record["city"])
        self.assertIsNone(record["asn"])


if __name__ == "__main__":
    unittest.main()
