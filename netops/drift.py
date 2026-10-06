"""Compare running configs to expected configs (drift detection)."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from netops.config import DRIFT_IGNORE_PATTERNS, EXPECTED_DIR, REPORTS_DIR, RUNNING_DIR, ensure_dirs


def normalize_config_text(text: str) -> list[str]:
    """Strip noise so diffs focus on intentional policy drift."""
    compiled = [re.compile(p) for p in DRIFT_IGNORE_PATTERNS]
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.strip() == "!":
            continue
        if any(p.search(line) for p in compiled):
            continue
        # Collapse multiple spaces
        line = re.sub(r"\s+", " ", line.strip())
        lines.append(line)
    return lines


@dataclass
class HostDrift:
    hostname: str
    has_drift: bool
    missing_expected: bool = False
    missing_running: bool = False
    diff_lines: list[str] = field(default_factory=list)


@dataclass
class DriftReport:
    generated_at: str
    hosts: list[HostDrift] = field(default_factory=list)

    @property
    def drifted(self) -> list[HostDrift]:
        return [h for h in self.hosts if h.has_drift]

    @property
    def ok(self) -> bool:
        return not self.drifted


def compare_host(hostname: str, expected: Path, running: Path) -> HostDrift:
    if not expected.exists():
        return HostDrift(hostname, True, missing_expected=True, diff_lines=["EXPECTED FILE MISSING"])
    if not running.exists():
        return HostDrift(hostname, True, missing_running=True, diff_lines=["RUNNING FILE MISSING"])

    exp = normalize_config_text(expected.read_text(encoding="utf-8"))
    run = normalize_config_text(running.read_text(encoding="utf-8"))
    diff = list(
        difflib.unified_diff(
            exp,
            run,
            fromfile=f"expected/{hostname}.cfg",
            tofile=f"running/{hostname}.cfg",
            lineterm="",
        )
    )
    return HostDrift(hostname, bool(diff), diff_lines=diff)


def scan_drift(
    expected_dir: Path | None = None,
    running_dir: Path | None = None,
    hostnames: list[str] | None = None,
) -> DriftReport:
    ensure_dirs()
    exp_dir = expected_dir or EXPECTED_DIR
    run_dir = running_dir or RUNNING_DIR
    report = DriftReport(generated_at=datetime.now(timezone.utc).isoformat())

    if hostnames:
        names = hostnames
    else:
        names = sorted({p.stem for p in exp_dir.glob("*.cfg")} | {p.stem for p in run_dir.glob("*.cfg")})

    for name in names:
        report.hosts.append(compare_host(name, exp_dir / f"{name}.cfg", run_dir / f"{name}.cfg"))
    return report


def write_markdown_report(report: DriftReport, path: Path | None = None) -> Path:
    ensure_dirs()
    out = path or (REPORTS_DIR / f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md")
    lines = [
        f"# Drift report",
        f"",
        f"- Generated at: `{report.generated_at}`",
        f"- Hosts checked: **{len(report.hosts)}**",
        f"- Hosts with drift: **{len(report.drifted)}**",
        f"- Status: **{'OK' if report.ok else 'DRIFT DETECTED'}**",
        f"",
    ]
    if report.ok:
        lines.append("No configuration drift detected.")
    else:
        for host in report.drifted:
            lines.append(f"## {host.hostname}")
            lines.append("")
            lines.append("```diff")
            lines.extend(host.diff_lines[:400])
            if len(host.diff_lines) > 400:
                lines.append(f"... ({len(host.diff_lines) - 400} more lines)")
            lines.append("```")
            lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
