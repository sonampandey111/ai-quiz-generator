#!/usr/bin/env python3
"""Entry point: python main.py "Your topic" [options]"""

import sys

from quiz_generator.cli import main

if __name__ == "__main__":
    sys.exit(main())
