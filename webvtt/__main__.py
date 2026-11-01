"""Run the command line interface with ``python -m webvtt``."""

import sys

from .cli import main

if __name__ == '__main__':
    sys.exit(main())
