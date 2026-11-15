"""Command-line interface of CincoIP.

This module reads the options from the command line. It then calls the
other modules in sequence:
    1. api_client  gets the public addresses of the computer.
    2. validators  examines each address.
    3. geo         gets the location and the network owner.
    4. formatter   makes the output for the terminal.
    5. exporter    saves the report, if the user gives a file name.

Feature owner: Aaron Christopher S. Ramos (branch feature/cli-integration).
"""

import argparse
import datetime
import sys

from cincoip import APP_NAME, __version__
from cincoip import api_client, exporter, formatter, geo, validators

OWN_LABELS = {4: "Public IPv4", 6: "Public IPv6"}

EXAMPLES = """examples:
  python main.py                     show the public IPv4 and IPv6 addresses
  python main.py -4                  show only the public IPv4 address
  python main.py --ip 8.8.8.8        look up an address that you give
  python main.py --json              print the report as JSON
  python main.py --save report.csv   save the report (.txt, .json, or .csv)
"""


def build_parser():
    """Return the parser that defines the command-line options."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "%s shows the public IPv4 and IPv6 addresses of this computer, "
            "with the location, the ISP, and the ASN of each address."
            % APP_NAME
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # The user can select only one of these two options.
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-4", "--ipv4-only", action="store_true",
        help="show only the public IPv4 address",
    )
    group.add_argument(
        "-6", "--ipv6-only", action="store_true",
        help="show only the public IPv6 address",
    )
    parser.add_argument(
        "--ip", action="append", metavar="ADDRESS",
        help=(
            "look up this address and not the addresses of this computer "
            "(you can use this option more than one time)"
        ),
    )
    parser.add_argument(
        "--no-geo", action="store_true",
        help="do not get the location, the ISP, and the ASN",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="print the report as JSON",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="print the table without colors",
    )
    parser.add_argument(
        "--save", metavar="FILE",
        help="save the report to FILE (.txt, .json, or .csv)",
    )
    parser.add_argument(
        "--version", action="version",
        version="%s %s" % (APP_NAME, __version__),
    )
    return parser


def make_record(label, address, version=None, error=None, want_geo=True):
    """Return the record of one address.

    Refer to cincoip/formatter.py for the keys of the record.
    """
    record = {
        "label": label,
        "address": address,
        "version": version,
        "category": None,
        "error": error,
        "geo": None,
        "geo_error": None,
    }
    if address is None:
        return record

    record["version"] = validators.ip_version(address)
    record["category"] = validators.classify_ip(address)
    if not want_geo:
        return record

    # Location APIs have data only for public addresses. Do not send a
    # private address to an external API.
    if record["category"] != "public":
        record["geo_error"] = (
            "Not available for an address of the type '%s'"
            % record["category"]
        )
        return record

    try:
        record["geo"] = geo.lookup(address)
    except api_client.ApiError as error_detail:
        record["geo_error"] = "Not available (%s)" % error_detail
    return record


def collect_own(versions, want_geo=True):
    """Return the records of the public addresses of this computer.

    versions: a list that contains 4, 6, or the two numbers.
    """
    records = []
    for version in versions:
        result = api_client.fetch_public_ip(version)
        records.append(
            make_record(
                OWN_LABELS[version],
                result["address"],
                version=version,
                error=result["error"],
                want_geo=want_geo,
            )
        )
    return records


def collect_given(addresses, want_geo=True):
    """Return the records of the addresses that the user gave."""
    records = []
    for text in addresses:
        try:
            address = validators.normalize_ip(text)
        except ValueError as error_detail:
            records.append(
                make_record(
                    "Lookup: %s" % str(text).strip(),
                    None,
                    error=str(error_detail),
                )
            )
            continue
        records.append(
            make_record("Lookup: %s" % address, address, want_geo=want_geo)
        )
    return records


def _prepare_output():
    """Prevent a stop of the program on a character that the terminal
    cannot show.

    Some city names contain characters that are not in the character set
    of the terminal. With this setting, Python prints "?" for such a
    character.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv=None):
    """Run the application and return the exit code.

    argv: a list of options for tests, or None to read the command line.

    Exit codes: 0 = the report contains a minimum of one address.
                1 = the report contains no address, or the save failed.
                2 = the options are not correct (argparse sets this code).
    """
    args = build_parser().parse_args(argv)
    _prepare_output()
    want_geo = not args.no_geo

    if args.ip:
        records = collect_given(args.ip, want_geo)
    else:
        if args.ipv4_only:
            versions = [4]
        elif args.ipv6_only:
            versions = [6]
        else:
            versions = [4, 6]
        records = collect_own(versions, want_geo)

    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if args.json:
        print(formatter.format_json(records, generated))
    else:
        use_color = (not args.no_color) and formatter.supports_color()
        print(formatter.format_text(records, generated, use_color))

    if args.save:
        try:
            kind = exporter.save_report(records, args.save, generated)
        except OSError as error_detail:
            print(
                "The report was not saved: %s" % error_detail,
                file=sys.stderr,
            )
            return 1
        # Use the error stream for this message. The JSON on the standard
        # output then stays valid.
        print(
            "Report saved to %s (%s format)." % (args.save, kind),
            file=sys.stderr,
        )

    if any(record["address"] for record in records):
        return 0
    return 1
