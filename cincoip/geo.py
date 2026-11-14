"""Location and network-owner lookup of CincoIP.

This module gets the location, the internet service provider (ISP), and
the autonomous system number (ASN) of a public IP address.

The module uses two location APIs. If the first API fails, the module
tries the second API. Each API has different key names, thus one function
for each API changes the reply into one standard dictionary.

Feature owner: Martin Raymund C. Piñol (branch feature/geo-lookup).

HOW TO ADD A LOCATION API
1. Write a function that accepts an address and returns a dictionary with
   the keys in GEO_KEYS. Raise ApiError if the API gives no data.
2. Add the name and the function to PROVIDERS.
3. Add a test to tests/test_geo.py.
"""

import ipaddress

from cincoip.api_client import ApiError, get_json

# Each provider function returns a dictionary with these keys.
# The value is None when the API has no data for a key.
GEO_KEYS = (
    "city",
    "region",
    "country",
    "country_code",
    "latitude",
    "longitude",
    "timezone",
    "utc_offset",
    "isp",
    "org",
    "asn",
)


def format_asn(value):
    """Return an ASN in the standard form, for example "AS15169".

    Some APIs send the ASN as a number (15169). Other APIs send text
    ("AS15169").
    """
    if value is None or value == "":
        return None
    text = str(value).strip().upper()
    if not text.startswith("AS"):
        text = "AS" + text
    return text


def _from_ipwhois(address):
    """Get data from the ipwho.is API (https://ipwhois.io/documentation).

    The free endpoint uses no API key.
    """
    data = get_json("https://ipwho.is/" + address)
    # This API sends HTTP status 200 for some errors. The "success" key
    # shows the result of the lookup.
    if not data.get("success", False):
        raise ApiError(data.get("message") or "the lookup failed")
    connection = data.get("connection") or {}
    timezone = data.get("timezone") or {}
    return {
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country"),
        "country_code": data.get("country_code"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": timezone.get("id"),
        "utc_offset": timezone.get("utc"),
        "isp": connection.get("isp"),
        "org": connection.get("org"),
        "asn": format_asn(connection.get("asn")),
    }


def _from_ipapi(address):
    """Get data from the ipapi.co API (https://ipapi.co/api/).

    The free endpoint uses no API key.
    """
    data = get_json("https://ipapi.co/%s/json/" % address)
    # This API sends HTTP status 200 for some errors. The "error" key
    # shows that the lookup failed.
    if data.get("error"):
        raise ApiError(data.get("reason") or "the lookup failed")
    return {
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name"),
        "country_code": data.get("country_code"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "utc_offset": data.get("utc_offset"),
        # This API gives one name for the network owner. Use the name for
        # the ISP and for the organization.
        "isp": data.get("org"),
        "org": data.get("org"),
        "asn": format_asn(data.get("asn")),
    }


# The application tries the providers in this sequence.
PROVIDERS = (
    ("ipwho.is", _from_ipwhois),
    ("ipapi.co", _from_ipapi),
)


def lookup(address):
    """Return the location data of one public IP address.

    The result is a dictionary with the keys in GEO_KEYS and the key
    "source". The "source" key gives the name of the API that sent the
    data.

    The function raises ValueError if the address is not valid.
    The function raises ApiError if all the providers fail.
    """
    # The address becomes a part of the URL. Use the standard form to
    # make sure that the URL contains only an IP address.
    address = str(ipaddress.ip_address(str(address).strip()))

    errors = []
    for name, provider in PROVIDERS:
        try:
            record = provider(address)
        except ApiError as error:
            errors.append("%s: %s" % (name, error))
            continue
        record["source"] = name
        return record
    raise ApiError(" | ".join(errors))
