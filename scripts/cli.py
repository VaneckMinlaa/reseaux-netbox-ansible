#!/usr/bin/env python3
"""CLI entrypoint: generate / validate / drift / pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as `python scripts/cli.py` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from netops.config import SOURCE_MODE, ensure_dirs
from netops.drift import scan_drift, write_markdown_report
from netops.render import generate_all, normalize_device
from netops.source import load_devices
from netops.validate import validate_devices


def cmd_generate(args: argparse.Namespace) -> int:
    devices = load_devices(site_filter=args.site, hostname_filter=args.host)
    if not devices:
        print("No devices found for the given filters.")
        return 1
    paths = generate_all(devices)
    print(f"Source mode: {SOURCE_MODE}")
    print(f"Generated {len(paths)} config(s):")
    for path in paths:
        print(f"  - {path}")
    if args.export_inventory:
        inv = {"all": {"children": {"switches": {"hosts": {}}}}}
        hosts = inv["all"]["children"]["switches"]["hosts"]
        for device in devices:
            data = normalize_device(device)
            hosts[data["hostname"]] = {
                "ansible_host": data["ansible_host"],
                "platform": data["platform"],
                "site": data["site"],
                "role": data["role"],
            }
        out = Path(args.export_inventory)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(inv, indent=2) + "\n", encoding="utf-8")
        print(f"Inventory exported: {out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    devices = load_devices(site_filter=args.site, hostname_filter=args.host)
    report = validate_devices(devices)
    for finding in report.findings:
        print(f"[{finding.severity.upper()}] {finding.hostname}: {finding.message}")
    if report.ok:
        print(f"Validation OK ({len(devices)} device(s)).")
        return 0
    print(f"Validation FAILED with {len(report.errors)} error(s).")
    return 2


def cmd_drift(args: argparse.Namespace) -> int:
    ensure_dirs()
    hostnames = [args.host] if args.host else None
    report = scan_drift(hostnames=hostnames)
    md = write_markdown_report(report)
    print(f"Report: {md}")
    if report.ok:
        print("No drift detected.")
        return 0
    print(f"DRIFT on {len(report.drifted)} host(s):")
    for host in report.drifted:
        print(f"  - {host.hostname} ({len(host.diff_lines)} diff lines)")
    return 3


def cmd_pipeline(args: argparse.Namespace) -> int:
    """generate → validate (used by CI)."""
    rc = cmd_generate(args)
    if rc != 0:
        return rc
    return cmd_validate(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Network config standardization toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_filters(p: argparse.ArgumentParser) -> None:
        p.add_argument("--site", help="Filter by site slug (e.g. pilote)")
        p.add_argument("--host", help="Filter by hostname")

    p_gen = sub.add_parser("generate", help="Render expected configs from NetBox/demo")
    add_filters(p_gen)
    p_gen.add_argument(
        "--export-inventory",
        help="Optional path to write a JSON inventory snippet for Ansible",
    )
    p_gen.set_defaults(func=cmd_generate)

    p_val = sub.add_parser("validate", help="Validate expected configs")
    add_filters(p_val)
    p_val.set_defaults(func=cmd_validate)

    p_drift = sub.add_parser("drift", help="Compare running vs expected")
    p_drift.add_argument("--host", help="Single hostname")
    p_drift.set_defaults(func=cmd_drift)

    p_pipe = sub.add_parser("pipeline", help="generate + validate")
    add_filters(p_pipe)
    p_pipe.add_argument("--export-inventory", default=None)
    p_pipe.set_defaults(func=cmd_pipeline)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
