"""Validation functions of CincoIP.

This module makes sure that text is a correct IP address. It also gives
the category of an address (for example public, private, or loopback).
The module uses only the "ipaddress" module of the Python standard library.
It sends no network requests.

Feature owner: Shean Terrence M. Bondoc (branch feature/validators).
"""

import ipaddress

# RFC 6598 keeps this IPv4 range for carrier-grade NAT (CGNAT).
# An internet service provider gives these addresses to its customers when
# many customers share one public address.
SHARED_NETWORK = ipaddress.ip_network("100.64.0.0/10")


def parse_ip(text):
    """Change text into an IP address object.

    The function raises ValueError with a clear message if the text is not
    a valid IPv4 address or IPv6 address.
    """
    if not isinstance(text, str):
        raise ValueError("The address must be text.")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("The address is empty.")
    try:
        return ipaddress.ip_address(cleaned)
    except ValueError:
        raise ValueError(
            "'%s' is not a valid IPv4 or IPv6 address." % cleaned
        ) from None


def is_valid_ip(text):
    """Return True if the text is a valid IPv4 address or IPv6 address."""
    try:
        parse_ip(text)
    except ValueError:
        return False
    return True


def ip_version(text):
    """Return 4 for an IPv4 address, or 6 for an IPv6 address."""
    return parse_ip(text).version


def normalize_ip(text):
    """Return the address in its standard short form.

    Example: "2001:0db8:0000:0000:0000:0000:0000:0001" becomes
    "2001:db8::1".
    """
    return str(parse_ip(text))


def classify_ip(text):
    """Return the category of an IP address as text.

    The possible results are: "unspecified", "loopback", "link-local",
    "multicast", "shared (CGNAT)", "reserved", "private", and "public".

    The sequence of the checks is important. Some special ranges are also
    part of the larger private range, thus the special ranges come first.
    """
    address = parse_ip(text)
    if address.is_unspecified:
        return "unspecified"
    if address.is_loopback:
        return "loopback"
    if address.is_link_local:
        return "link-local"
    if address.is_multicast:
        return "multicast"
    if address.version == 4 and address in SHARED_NETWORK:
        return "shared (CGNAT)"
    if address.is_reserved:
        return "reserved"
    if address.is_private:
        return "private"
    return "public"


def is_public(text):
    """Return True if a location lookup is possible for the address.

    Location APIs have data only for public addresses.
    """
    return classify_ip(text) == "public"
