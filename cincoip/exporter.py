"""File export functions of CincoIP.

This module saves the report to a file. The extension of the file name
sets the format:
    .json  JSON text
    .csv   one row for each address (a spreadsheet can open this file)
    other  the same table that the terminal shows, without colors

Feature owner: Arnold Janssen S. Martinez (branch feature/export-docs).
"""

import csv
import os

from cincoip.formatter import format_json, format_text
from cincoip.geo import GEO_KEYS

# The columns of the CSV file, in sequence.
CSV_COLUMNS = (
    ("label", "address", "version", "category")
    + GEO_KEYS
    + ("source", "error", "geo_error")
)


def detect_format(path):
    """Return "json", "csv", or "text" for a file name."""
    extension = os.path.splitext(path)[1].lower()
    if extension == ".json":
        return "json"
    if extension == ".csv":
        return "csv"
    return "text"


def flatten_record(record):
    """Return one record as a flat dictionary for the CSV file.

    The record contains the location data as a second dictionary. A CSV
    row cannot contain a dictionary, thus this function moves the location
    keys to the first level.
    """
    geo = record.get("geo") or {}
    row = {}
    for column in CSV_COLUMNS:
        if column in GEO_KEYS or column == "source":
            row[column] = geo.get(column)
        else:
            row[column] = record.get(column)
    return row


def save_report(records, path, generated=None):
    """Save the report to a file and return the name of the format.

    records:   a list of record dictionaries.
    path:      the name of the file.
    generated: the date and time of the report as text, or None.

    The function raises OSError if the computer cannot write the file.
    """
    kind = detect_format(path)
    if kind == "csv":
        # The csv module controls the line ends. Thus newline must be "".
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for record in records:
                writer.writerow(flatten_record(record))
        return kind

    if kind == "json":
        text = format_json(records, generated)
    else:
        text = format_text(records, generated, use_color=False)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    return kind
