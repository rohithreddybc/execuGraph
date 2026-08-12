#!/usr/bin/env python
"""Thin wrapper around ``execugraph.runner.cli.main``.

Kept as a top-level script so users can run ``python scripts/run_experiment.py``
without first installing the package.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running before ``pip install -e .``
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execugraph.runner.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
