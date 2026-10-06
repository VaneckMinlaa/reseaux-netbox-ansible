"""Validate generated (expected) configurations against policy rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from netops.config import EXPECTED_DIR
from netops.render import normalize_device


@dataclass
class Finding:
    hostname: str
    severity: str  # error | warning
    message: str


@dataclass
class ValidationReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, hostname: str, severity: str, message: str) -> None:
        self.findings.append(Finding(hostname, severity, message))


def validate_rendered_text(hostname: str, text: str, device: dict[str, Any] | None = None) -> list[Finding]:
    findings: list[Finding] = []

    if not text.strip():
        findings.append(Finding(hostname, "error", "Config is empty"))
        return findings

    if "{{" in text or "{%" in text:
        findings.append(Finding(hostname, "error", "Unrendered Jinja2 markers remain"))

    if not re.search(r"(?im)^hostname\s+\S+", text) and not re.search(
        r"(?im)^hostname\s+\S+", text.replace("!", "")
    ):
        # Cisco: hostname X / Arista: hostname X
        if "hostname" not in text.lower():
            findings.append(Finding(hostname, "error", "Missing hostname"))

    if hostname not in text:
        findings.append(Finding(hostname, "warning", f"Hostname '{hostname}' not found in config body"))

    # No leftover TODO
    if "TODO" in text or "FIXME" in text:
        findings.append(Finding(hostname, "error", "TODO/FIXME left in generated config"))

    if device:
        data = normalize_device(device)
        for vlan in data["vlans"]:
            vid = str(vlan["id"])
            if vid not in text:
                findings.append(
                    Finding(hostname, "error", f"VLAN {vid} ({vlan.get('name')}) missing from config")
                )
        for iface in data["interfaces"]:
            if iface["name"] not in text:
                findings.append(
                    Finding(hostname, "warning", f"Interface {iface['name']} not present in config")
                )
            if iface["mode"] == "access" and iface.get("vlan") and not iface.get("description"):
                findings.append(
                    Finding(
                        hostname,
                        "warning",
                        f"Interface {iface['name']} has no description",
                    )
                )

        # Uplink trunks should allow defined VLANs only
        vlan_ids = {int(v["id"]) for v in data["vlans"]}
        for iface in data["interfaces"]:
            if iface["mode"] == "trunk":
                for vid in iface.get("allowed_vlans") or []:
                    if int(vid) not in vlan_ids:
                        findings.append(
                            Finding(
                                hostname,
                                "error",
                                f"Trunk {iface['name']} allows VLAN {vid} not defined on device/site",
                            )
                        )

    return findings


def validate_devices(devices: list[dict[str, Any]], expected_dir: Path | None = None) -> ValidationReport:
    report = ValidationReport()
    base = expected_dir or EXPECTED_DIR
    for device in devices:
        data = normalize_device(device)
        path = base / f"{data['hostname']}.cfg"
        if not path.exists():
            report.add(data["hostname"], "error", f"Missing expected config: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for finding in validate_rendered_text(data["hostname"], text, device):
            report.findings.append(finding)
    return report
