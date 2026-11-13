"""Tests of cincoip/api_client.py.

These tests send no network requests. The "mock" object replaces
requests.get and gives a prepared reply.
"""

import unittest
from unittest import mock

import requests

from cincoip import api_client


def fake_response(status_code=200, json_data=None, json_error=False):
    """Return an object that operates as a requests response."""
    response = mock.Mock()
    response.status_code = status_code
    if json_error:
        response.json.side_effect = ValueError("no JSON")
    else:
        response.json.return_value = json_data
    return response


class GetJsonTests(unittest.TestCase):
    @mock.patch("cincoip.api_client.requests.get")
    def test_returns_the_dictionary(self, fake_get):
        fake_get.return_value = fake_response(json_data={"ip": "8.8.8.8"})
        self.assertEqual(api_client.get_json("https://x"), {"ip": "8.8.8.8"})

    @mock.patch("cincoip.api_client.requests.get")
    def test_sends_timeout_and_user_agent(self, fake_get):
        fake_get.return_value = fake_response(json_data={})
        api_client.get_json("https://x")
        arguments = fake_get.call_args[1]
        self.assertEqual(arguments["timeout"], api_client.TIMEOUT_SECONDS)
        self.assertIn("User-Agent", arguments["headers"])

    @mock.patch("cincoip.api_client.requests.get")
    def test_timeout_raises_api_error(self, fake_get):
        fake_get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(api_client.ApiError):
            api_client.get_json("https://x")

    @mock.patch("cincoip.api_client.requests.get")
    def test_connection_failure_raises_api_error(self, fake_get):
        fake_get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(api_client.ApiError):
            api_client.get_json("https://x")

    @mock.patch("cincoip.api_client.requests.get")
    def test_error_status_includes_the_reason(self, fake_get):
        # ipapi.co sends this body when the daily quota is used.
        fake_get.return_value = fake_response(
            status_code=429, json_data={"error": True, "reason": "RateLimited"}
        )
        with self.assertRaises(api_client.ApiError) as context:
            api_client.get_json("https://x")
        self.assertIn("429", str(context.exception))
        self.assertIn("RateLimited", str(context.exception))

    @mock.patch("cincoip.api_client.requests.get")
    def test_reply_that_is_not_json_raises_api_error(self, fake_get):
        fake_get.return_value = fake_response(json_error=True)
        with self.assertRaises(api_client.ApiError):
            api_client.get_json("https://x")

    @mock.patch("cincoip.api_client.requests.get")
    def test_json_list_raises_api_error(self, fake_get):
        fake_get.return_value = fake_response(json_data=["8.8.8.8"])
        with self.assertRaises(api_client.ApiError):
            api_client.get_json("https://x")


class FetchPublicIpTests(unittest.TestCase):
    @mock.patch("cincoip.api_client.get_json")
    def test_ipv4_address(self, fake_get_json):
        fake_get_json.return_value = {"ip": "203.0.113.7"}
        result = api_client.fetch_public_ip(4)
        self.assertEqual(result["address"], "203.0.113.7")
        self.assertIsNone(result["error"])
        self.assertEqual(
            fake_get_json.call_args[0][0], "https://api.ipify.org"
        )

    @mock.patch("cincoip.api_client.get_json")
    def test_ipv6_address_uses_the_ipv6_host(self, fake_get_json):
        fake_get_json.return_value = {"ip": "2001:4860:4860::8888"}
        result = api_client.fetch_public_ip(6)
        self.assertEqual(result["address"], "2001:4860:4860::8888")
        self.assertEqual(
            fake_get_json.call_args[0][0], "https://api6.ipify.org"
        )

    @mock.patch("cincoip.api_client.get_json")
    def test_no_ipv6_connection_gives_a_clear_message(self, fake_get_json):
        fake_get_json.side_effect = api_client.ApiError("connection failed")
        result = api_client.fetch_public_ip(6)
        self.assertIsNone(result["address"])
        self.assertIn("IPv6 is not available", result["error"])

    @mock.patch("cincoip.api_client.get_json")
    def test_ipv4_failure_gives_a_message(self, fake_get_json):
        fake_get_json.side_effect = api_client.ApiError("connection failed")
        result = api_client.fetch_public_ip(4)
        self.assertIsNone(result["address"])
        self.assertIn("IPv4 lookup failed", result["error"])

    @mock.patch("cincoip.api_client.get_json")
    def test_text_that_is_not_an_address_is_rejected(self, fake_get_json):
        fake_get_json.return_value = {"ip": "<html>error</html>"}
        result = api_client.fetch_public_ip(4)
        self.assertIsNone(result["address"])
        self.assertIsNotNone(result["error"])

    @mock.patch("cincoip.api_client.get_json")
    def test_incorrect_ip_version_is_rejected(self, fake_get_json):
        fake_get_json.return_value = {"ip": "203.0.113.7"}
        result = api_client.fetch_public_ip(6)
        self.assertIsNone(result["address"])
        self.assertIn("IPv4", result["error"])

    def test_version_must_be_4_or_6(self):
        with self.assertRaises(ValueError):
            api_client.fetch_public_ip(5)


if __name__ == "__main__":
    unittest.main()
