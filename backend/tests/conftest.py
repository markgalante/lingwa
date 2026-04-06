"""Shared pytest configuration.

Adds backend/scripts/ to sys.path so test modules can import build scripts
(e.g. build_nl_dict) as regular modules without packaging them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
