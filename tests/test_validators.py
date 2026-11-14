"""Tests of cincoip/validators.py."""

import unittest

from cincoip import validators


class ParseTests(unittest.TestCase):
    def test_valid_addresses(self):
        for text in ("8.8.8.8", "192.168.1.1", "::1", "2001:4860:4860::8888"):
            self.assertTrue(validators.is_valid_ip(text), text)

    def test_spaces_around_the_address_are_permitted(self):
        self.assertTrue(validators.is_valid_ip("  8.8.8.8  "))

    def test_text_that_is_not_an_address(self):
        for text in ("", "   ", "256.1.1.1", "8.8.8", "example.com",
                     "8.8.8.8/24", "8.8.8.8/../admin", "1.2.3.4.5"):
            self.assertFalse(validators.is_valid_ip(text), text)

    def test_value_that_is_not_text(self):
        self.assertFalse(validators.is_valid_ip(None))
        self.assertFalse(validators.is_valid_ip(8888))

    def test_error_message_names_the_text(self):
        with self.assertRaises(ValueError) as context:
            validators.parse_ip("abc")
        self.assertIn("abc", str(context.exception))

    def test_ip_version(self):
        self.assertEqual(validators.ip_version("8.8.8.8"), 4)
        self.assertEqual(validators.ip_version("2001:db8::1"), 6)

    def test_normalize_gives_the_short_form(self):
        self.assertEqual(
            validators.normalize_ip("2001:0db8:0000:0000:0000:0000:0000:0001"),
            "2001:db8::1",
        )
        self.assertEqual(validators.normalize_ip(" 8.8.8.8 "), "8.8.8.8")


class ClassifyTests(unittest.TestCase):
    def test_categories(self):
        expected = {
            "8.8.8.8": "public",
            "2001:4860:4860::8888": "public",
            "10.0.0.1": "private",
            "172.16.5.4": "private",
            "192.168.1.1": "private",
            "fd00::1": "private",
            "127.0.0.1": "loopback",
            "::1": "loopback",
            "169.254.10.10": "link-local",
            "fe80::1": "link-local",
            "224.0.0.1": "multicast",
            "ff02::1": "multicast",
            "0.0.0.0": "unspecified",
            "::": "unspecified",
            "100.64.0.1": "shared (CGNAT)",
            "100.127.255.254": "shared (CGNAT)",
            "240.0.0.1": "reserved",
        }
        for text, category in expected.items():
            self.assertEqual(validators.classify_ip(text), category, text)

    def test_addresses_next_to_the_cgnat_range_are_public(self):
        self.assertEqual(validators.classify_ip("100.63.255.255"), "public")
        self.assertEqual(validators.classify_ip("100.128.0.0"), "public")

    def test_is_public(self):
        self.assertTrue(validators.is_public("1.1.1.1"))
        self.assertFalse(validators.is_public("192.168.0.10"))
        self.assertFalse(validators.is_public("100.64.0.1"))

    def test_classify_rejects_text_that_is_not_an_address(self):
        with self.assertRaises(ValueError):
            validators.classify_ip("not-an-ip")


if __name__ == "__main__":
    unittest.main()
