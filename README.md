# CincoIP

CincoIP is a Python command-line application for network technicians. It shows the public IPv4 address and the public IPv6 address of the computer. For each address, it also shows the location, the internet service provider (ISP), the autonomous system number (ASN), and the country code.

Team Cinco De Mayo made this application for DEVASC Project Activity 3 (Social Coding), Option 2: New Code - Create an IPv4/IPv6 Address Application.

## Features

| No. | Feature | Module |
|---|---|---|
| 1 | Shows the public IPv4 address of the computer. | `cincoip/api_client.py` |
| 2 | Shows the public IPv6 address of the computer. If the network has no IPv6 connection, the application gives a clear message and continues. | `cincoip/api_client.py` |
| 3 | Shows the city, region, country, country code, coordinates, time zone, ISP, organization, and ASN of each public address. A second API is the fallback if the first API fails. | `cincoip/geo.py` |
| 4 | Looks up an address that the user gives (`--ip`). The application examines the address before it sends a request. It does not send private addresses to an external API. | `cincoip/validators.py` |
| 5 | Prints an aligned table with colors. The colors go off automatically when the output goes to a file. | `cincoip/formatter.py` |
| 6 | Prints the report as JSON (`--json`) for use by other programs. | `cincoip/formatter.py` |
| 7 | Saves the report to a text file, a JSON file, or a CSV file (`--save`). | `cincoip/exporter.py` |
| 8 | Has 70 unit tests that send no network requests. | `tests/` |

## Requirements

- Python 3.8 or later. The team did tests on Python 3.8 and Python 3.13.
- The `requests` library.
- An internet connection.
- No API key is necessary.

## Installation

1. Clone the repository.

   ```
   git clone https://github.com/aaron-c-s-ramos/devasc-cincoip.git
   cd devasc-cincoip
   ```

2. Install the library.

   ```
   python -m pip install -r requirements.txt
   ```

On Linux and macOS, use `python3` if the `python` command is not available.

## Usage

```
python main.py [-h] [-4 | -6] [--ip ADDRESS] [--no-geo] [--json] [--no-color] [--save FILE] [--version]
```

| Option | Function |
|---|---|
| no option | Shows the public IPv4 and IPv6 addresses of the computer with all data. |
| `-4`, `--ipv4-only` | Shows only the public IPv4 address. |
| `-6`, `--ipv6-only` | Shows only the public IPv6 address. |
| `--ip ADDRESS` | Looks up the address that you give. You can use this option more than one time. |
| `--no-geo` | Shows only the addresses. The application sends no location requests. |
| `--json` | Prints the report as JSON. |
| `--no-color` | Prints the table without colors. |
| `--save FILE` | Saves the report. The extension sets the format: `.json`, `.csv`, or text for all other extensions. |
| `--version` | Shows the version of the application. |
| `-h`, `--help` | Shows the help text. |

Examples:

```
python main.py
python main.py -4
python main.py --ip 8.8.8.8 --ip 2001:4860:4860::8888
python main.py --json --save report.json
python main.py --save report.csv
```

Exit codes: `0` = the report contains a minimum of one address. `1` = the report contains no address, or the save failed. `2` = the options are not correct.

## Sample output

Command: `python main.py --ip 8.8.8.8`

```
CincoIP 1.0.0 - IP address report
Generated: 2026-11-12 21:34:17 (local time)

+-------------------------------------------------+
| Lookup: 8.8.8.8                                 |
+--------------+----------------------------------+
| Address      | 8.8.8.8                          |
| IP version   | IPv4                             |
| Address type | Public                           |
| City         | San Jose                         |
| Region       | California                       |
| Country      | United States (US)               |
| Coordinates  | 37.3393939, -121.8949553         |
| Time zone    | America/Los_Angeles (UTC -08:00) |
| ISP          | Google LLC                       |
| Organization | Google LLC                       |
| ASN          | AS15169                          |
| Data source  | ipwho.is                         |
+--------------+----------------------------------+
```

On a network that has no IPv6 connection, `python main.py` shows this table for IPv6:

```
+-----------------------------------------------------+
| Public IPv6                                         |
+--------+--------------------------------------------+
| Status | IPv6 is not available on this network (the |
|        | connection to the server failed)           |
+--------+--------------------------------------------+
```

## Structure of the project

```
devasc-cincoip/
├── main.py              Start file. Run this file.
├── requirements.txt     The necessary library.
├── README.md            This document.
├── cincoip/             The application package.
│   ├── __init__.py      Name and version of the application.
│   ├── api_client.py    HTTP requests and the public address lookup.
│   ├── validators.py    Address validation and address categories.
│   ├── geo.py           Location, ISP, and ASN lookup with fallback.
│   ├── formatter.py     Table output, colors, and JSON output.
│   ├── exporter.py      Save to text, JSON, or CSV.
│   └── cli.py           Command-line options and the sequence of the program.
├── tests/               One test file for each module.
└── docs/
    └── BACKLOG.md       Enhancements for a future revision.
```

| Module | Feature owner | Branch |
|---|---|---|
| `api_client.py` | Aaron Christopher S. Ramos | `feature/ip-lookup` |
| `geo.py` | Martin Raymund C. Piñol | `feature/geo-lookup` |
| `validators.py` | Shean Terrence M. Bondoc | `feature/validators` |
| `formatter.py` | Kristian Yuji M. Bagdoc | `feature/formatter` |
| `exporter.py`, `README.md`, `docs/BACKLOG.md` | Arnold Janssen S. Martinez | `feature/export-docs` |
| `cli.py`, `main.py` | Aaron Christopher S. Ramos | `feature/cli-integration` |

## How the application operates

1. `main.py` calls `cli.main()`.
2. `cli.py` reads the options with `argparse`.
3. `api_client.fetch_public_ip()` sends a request to the ipify API for each IP version. The ipify API replies with the address that it sees.
4. `validators.classify_ip()` gives the category of each address (for example public or private).
5. `geo.lookup()` sends each public address to a location API. If the first API fails, the function tries the second API.
6. `cli.make_record()` puts the data of each address into one dictionary (the record).
7. `formatter.py` changes the records into a table or into JSON. `cli.py` prints the result.
8. If the user gives `--save`, `exporter.save_report()` writes the file.

### The record

All the modules use the same dictionary for one address:

| Key | Content |
|---|---|
| `label` | Title of the table, for example `Public IPv4`. |
| `address` | The IP address as text, or `None`. |
| `version` | `4`, `6`, or `None`. |
| `category` | `public`, `private`, `loopback`, `link-local`, `multicast`, `shared (CGNAT)`, `reserved`, or `unspecified`. |
| `error` | The cause when there is no address, or `None`. |
| `geo` | The location dictionary, or `None`. Its keys are in `geo.GEO_KEYS`, plus `source`. |
| `geo_error` | The cause when there is no location data, or `None`. |

## The APIs

No API in this table uses an API key on its free endpoint.

| API | Use in CincoIP | Endpoint | Note from the API documentation |
|---|---|---|---|
| [ipify](https://www.ipify.org/) | Public IPv4 address | `https://api.ipify.org?format=json` | Replies with `{"ip": "..."}`. |
| [ipify](https://www.ipify.org/) | Public IPv6 address | `https://api6.ipify.org?format=json` | For IPv6 requests only. The request fails if the computer has no IPv6 address. |
| [ipwho.is](https://ipwhois.io/documentation) | Location, ISP, ASN (first API) | `https://ipwho.is/{address}` | Free limit: 1,000 requests each day for each client IP address. HTTP status 429 when the limit is exceeded. |
| [ipapi.co](https://ipapi.co/api/) | Location, ISP, ASN (fallback API) | `https://ipapi.co/{address}/json/` | HTTP status 429 with the reason `RateLimited` when the quota is exceeded. The documentation page does not give the free limit. |

## Tests

Run all the tests from the top folder of the project:

```
python -m unittest -v
```

The tests use `unittest.mock` to replace the API replies. Thus the tests operate without an internet connection, and they do not use the API quota. Each module has one test file with the same name (`cincoip/geo.py` and `tests/test_geo.py`).

## Known limits

- The location of an IP address is an estimate. It usually shows the city of the ISP equipment, not the address of the user.
- If the computer uses a VPN or a proxy, the application shows the address of the VPN or the proxy.
- Many Philippine networks have no IPv6 connection. On those networks, the IPv6 table shows the status message.
- A large number of users behind one shared address (for example on a campus network) can use the daily quota of a free API. The fallback API decreases this risk.

## How to continue the project

**Add a location API.** Refer to the instructions at the top of `cincoip/geo.py`. Write one function that returns the keys in `GEO_KEYS`, then add it to `PROVIDERS`.

**Add an output format.** Add a function to `cincoip/formatter.py` that accepts the list of records. Then add the extension to `detect_format()` and `save_report()` in `cincoip/exporter.py`.

**Add a command-line option.** Add the option in `build_parser()` in `cincoip/cli.py`. Then use the value in `main()`.

**Add a row to the table.** Add a tuple to `record_rows()` in `cincoip/formatter.py`.

For each change, add a test to the applicable file in `tests/`.

## Git workflow

1. The `main` branch always contains code that operates. Do not commit directly to `main`.
2. Make one branch for each feature: `git checkout -b feature/<name>`.
3. Commit small changes with clear messages.
4. Push the branch and open a pull request on GitHub.
5. A different team member reviews the pull request and runs the tests.
6. After the approval, merge the pull request and delete the branch.

## Backlog

Refer to [docs/BACKLOG.md](docs/BACKLOG.md) for the list of enhancements for a future revision.

## Team Cinco De Mayo

| Member | Role |
|---|---|
| Martin Raymund C. Piñol | Scrum Leader, developer |
| Kristian Yuji M. Bagdoc | Recorder, developer |
| Aaron Christopher S. Ramos | Technical Lead and Repository Maintainer, developer |
| Shean Terrence M. Bondoc | QA Tester, developer |
| Arnold Janssen S. Martinez | Documentation Lead, developer |

DEVASC, section 4ITB, University of Santo Tomas.
