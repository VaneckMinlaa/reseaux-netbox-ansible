"""Shared paths and environment loading."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SOURCE_MODE = os.getenv("SOURCE_MODE", "demo").lower()
NETBOX_URL = os.getenv("NETBOX_URL", "").rstrip("/")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "")

EXPECTED_DIR = ROOT / os.getenv("EXPECTED_DIR", "configs/expected")
RUNNING_DIR = ROOT / os.getenv("RUNNING_DIR", "configs/running")
REPORTS_DIR = ROOT / os.getenv("REPORTS_DIR", "reports")
TEMPLATES_DIR = ROOT / os.getenv("TEMPLATES_DIR", "templates")
DEMO_DATA = ROOT / "data" / "demo_devices.yaml"

# Lines / patterns ignored when comparing running vs expected (noise)
DRIFT_IGNORE_PATTERNS = [
    r"^!.*Last configuration change",
    r"^!.*NVRAM config last updated",
    r"^!.*No configuration change since last restart",
    r"^ntp clock-period\s+\d+",
    r"^cryptographic-algorithm\s+",
    r"^username .+ secret \d+ .+",
    r"^enable secret \d+ .+",
    r"^! Time:",
    r"^! Command:",
]


def ensure_dirs() -> None:
    for path in (EXPECTED_DIR, RUNNING_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
