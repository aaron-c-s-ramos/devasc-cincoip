"""Output functions of CincoIP.

This module changes the records of the application into text for the
terminal (a table with optional colors) or into JSON text.

Feature owner: Kristian Yuji M. Bagdoc (branch feature/formatter).

THE RECORD
The application keeps the data of one IP address in a dictionary. All the
modules use the same keys:
    "label":     the title of the table, for example "Public IPv4".
    "address":   the IP address as text, or None.
    "version":   4, 6, or None.
    "category":  the result of validators.classify_ip(), or None.
    "error":     the cause when there is no address, or None.
    "geo":       the dictionary from geo.lookup(), or None.
    "geo_error": the cause when there is no location data, or None.
"""

import json
import os
import sys
import textwrap

from cincoip import APP_NAME, __version__

# ANSI escape codes. A terminal reads these codes as color commands.
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

# The table uses only ASCII characters. Some Windows terminals cannot show
# box-drawing characters.
MINIMUM_VALUE_WIDTH = 30
MAXIMUM_VALUE_WIDTH = 48
EMPTY_VALUE = "-"


def supports_color(stream=None):
    """Return True if the output stream can show ANSI colors.

    The function returns False when the user sends the output to a file or
    to a different program. It also obeys the NO_COLOR environment variable
    (https://no-color.org).
    """
    if stream is None:
        stream = sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if os.name == "nt":
        # On Windows, an empty system command sets the terminal to accept
        # ANSI codes.
        os.system("")
    return True


def paint(text, code, use_color):
    """Return the text with a color code, or the same text without color."""
    if not use_color:
        return text
    return "%s%s%s" % (code, text, RESET)


def _show(value):
    """Return a value as text. Return a dash if there is no value."""
    if value is None or value == "":
        return EMPTY_VALUE
    return str(value)


def record_rows(record):
    """Return the table rows of one record.

    Each row is a tuple: (name, value, style). The style is "good",
    "warning", or "plain". The style sets the color of the value.
    """
    address = record.get("address")
    if not address:
        return [("Status", _show(record.get("error")), "warning")]

    rows = [
        ("Address", address, "good"),
        ("IP version", "IPv%s" % record.get("version"), "plain"),
        ("Address type", _show(record.get("category")).capitalize(), "plain"),
    ]

    geo = record.get("geo")
    if geo:
        country = _show(geo.get("country"))
        if geo.get("country_code"):
            country = "%s (%s)" % (country, geo["country_code"])

        coordinates = EMPTY_VALUE
        if geo.get("latitude") is not None and geo.get("longitude") is not None:
            coordinates = "%s, %s" % (geo["latitude"], geo["longitude"])

        timezone = _show(geo.get("timezone"))
        if geo.get("utc_offset"):
            timezone = "%s (UTC %s)" % (timezone, geo["utc_offset"])

        rows.extend(
            [
                ("City", _show(geo.get("city")), "plain"),
                ("Region", _show(geo.get("region")), "plain"),
                ("Country", country, "plain"),
                ("Coordinates", coordinates, "plain"),
                ("Time zone", timezone, "plain"),
                ("ISP", _show(geo.get("isp")), "plain"),
                ("Organization", _show(geo.get("org")), "plain"),
                ("ASN", _show(geo.get("asn")), "plain"),
                ("Data source", _show(geo.get("source")), "plain"),
            ]
        )
    elif record.get("geo_error"):
        rows.append(("Location data", record["geo_error"], "warning"))
    return rows


def format_record(record, use_color=False):
    """Return one record as a table with a title row."""
    rows = record_rows(record)
    title = _show(record.get("label"))

    # Divide a long value into two or more lines. The table then stays
    # in the width of a standard terminal (80 characters).
    wrapped_rows = []
    for name, value, style in rows:
        pieces = textwrap.wrap(value, MAXIMUM_VALUE_WIDTH) or [EMPTY_VALUE]
        wrapped_rows.append((name, pieces[0], style))
        for piece in pieces[1:]:
            wrapped_rows.append(("", piece, style))
    rows = wrapped_rows

    name_width = max(len(name) for name, _, _ in rows)
    value_width = max(
        [MINIMUM_VALUE_WIDTH] + [len(value) for _, value, _ in rows]
    )
    # The title row has the width of the two columns and the 3 characters
    # between them (" | ").
    inner_width = max(name_width + value_width + 3, len(title))
    value_width = inner_width - name_width - 3

    styles = {"good": GREEN, "warning": YELLOW, "plain": ""}
    full_line = "+" + "-" * (inner_width + 2) + "+"
    split_line = (
        "+" + "-" * (name_width + 2) + "+" + "-" * (value_width + 2) + "+"
    )

    lines = [
        full_line,
        "| " + paint(title.ljust(inner_width), BOLD + CYAN, use_color) + " |",
        split_line,
    ]
    for name, value, style in rows:
        # Add the spaces before the color codes. The color codes have no
        # width on the screen, but Python counts them as characters.
        padded = value.ljust(value_width)
        if styles[style]:
            padded = paint(padded, styles[style], use_color)
        lines.append("| " + name.ljust(name_width) + " | " + padded + " |")
    lines.append(split_line)
    return "\n".join(lines)


def format_text(records, generated=None, use_color=False):
    """Return the full report as text for the terminal or for a text file.

    records:   a list of record dictionaries.
    generated: the date and time of the report as text, or None.
    use_color: True to add ANSI color codes.
    """
    header = "%s %s - IP address report" % (APP_NAME, __version__)
    parts = [paint(header, BOLD, use_color)]
    if generated:
        parts.append("Generated: %s (local time)" % generated)
    for record in records:
        parts.append("")
        parts.append(format_record(record, use_color))
    return "\n".join(parts)


def format_json(records, generated=None):
    """Return the full report as JSON text.

    A different program can read this output. Example: python main.py --json
    """
    report = {
        "application": APP_NAME,
        "version": __version__,
        "generated": generated,
        "results": records,
    }
    return json.dumps(report, indent=2, ensure_ascii=False)
