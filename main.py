"""Start file of CincoIP.

Run this file to start the application:
    python main.py
    python main.py --help
"""

import sys

from cincoip.cli import main

if __name__ == "__main__":
    sys.exit(main())
