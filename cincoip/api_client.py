"""HTTP functions of CincoIP.

This module sends each HTTP request of the application. It also gets the
public IPv4 address and the public IPv6 address of the computer from the
ipify API (https://www.ipify.org).

Feature owner: Aaron Christopher S. Ramos (branch feature/ip-lookup).
"""

import ipaddress

import requests

# The ipify API has one host for each IP version.
# The IPv6 host has only an IPv6 address. Thus a request to that host fails
# on a network that has no IPv6 connection.
IPIFY_URLS = {
    4: "https://api.ipify.org",
    6: "https://api6.ipify.org",
}

# Maximum time, in seconds, that the application waits for one reply.
TIMEOUT_SECONDS = 8

# Some APIs reject a request that has no User-Agent header.
USER_AGENT = "CincoIP/1.0 (DEVASC class project)"


class ApiError(Exception):
    """An API request did not give data that the application can use."""


class ConnectivityApiError(ApiError):
    """An API request failed because the host could not be reached."""


def get_json(url, params=None, timeout=TIMEOUT_SECONDS):
    """Send an HTTP GET request and return the JSON reply as a dictionary.

    url:     the full address of the API endpoint.
    params:  an optional dictionary of query parameters.
    timeout: the maximum time for the reply, in seconds.

    The function raises ApiError for each failure. The caller thus uses
    only one "except" statement.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        response = requests.get(
            url, params=params, headers=headers, timeout=timeout
        )
    except requests.exceptions.Timeout:
        raise ConnectivityApiError(
            "the server did not answer in %d seconds" % timeout
        ) from None
    except requests.exceptions.ConnectionError:
        raise ConnectivityApiError(
            "the connection to the server failed"
        ) from None
    except requests.exceptions.RequestException as error:
        raise ApiError("the request failed: %s" % error) from None

    # An API can send the cause of an error as JSON together with an error
    # status code. Read the body before the check of the status code.
    try:
        data = response.json()
    except ValueError:
        data = None

    if response.status_code != 200:
        reason = ""
        if isinstance(data, dict):
            reason = data.get("reason") or data.get("message") or ""
        message = "HTTP status %d" % response.status_code
        if reason:
            message = "%s, %s" % (message, reason)
        raise ApiError(message)

    if not isinstance(data, dict):
        raise ApiError("the reply was not a JSON object")
    return data


def fetch_public_ip(version):
    """Get the public IP address of this computer for one IP version.

    version: 4 for IPv4, or 6 for IPv6.

    The function returns a dictionary with these keys:
        "version": the IP version that the caller gave.
        "address": the address as text, or None if there is no address.
        "error":   the cause of the failure as text, or None.

    The function does not raise ApiError. A network that has no IPv6
    connection is a usual condition, not a defect of the application.
    """
    if version not in IPIFY_URLS:
        raise ValueError("The IP version must be 4 or 6.")

    result = {"version": version, "address": None, "error": None}
    try:
        data = get_json(IPIFY_URLS[version], params={"format": "json"})
    except ApiError as error:
        if version == 6 and isinstance(error, ConnectivityApiError):
            result["error"] = (
                "IPv6 is not available on this network (%s)" % error
            )
        elif version == 6:
            result["error"] = "The IPv6 lookup failed (%s)" % error
        else:
            result["error"] = "The IPv4 lookup failed (%s)" % error
        return result

    # Do not trust the reply. Make sure that the text is an IP address of
    # the correct version.
    text = str(data.get("ip", "")).strip()
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        result["error"] = "The ipify API sent text that is not an IP address"
        return result
    if address.version != version:
        result["error"] = (
            "The ipify API sent an IPv%d address" % address.version
        )
        return result

    result["address"] = str(address)
    return result
