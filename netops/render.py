"""Normalize device intent and render Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from netops.config import EXPECTED_DIR, TEMPLATES_DIR, ensure_dirs


PLATFORM_TEMPLATE = {
    "cisco_ios": "cisco_ios/base.j2",
    "ios": "cisco_ios/base.j2",
    "arista_eos": "arista_eos/base.j2",
    "eos": "arista_eos/base.j2",
}


def normalize_device(device: dict[str, Any]) -> dict[str, Any]:
    """Ensure a stable schema for templates regardless of source."""
    platform = (device.get("platform") or "cisco_ios").lower().replace("-", "_")
    vlans = device.get("vlans") or []
    interfaces = []
    for iface in device.get("interfaces") or []:
        interfaces.append(
            {
                "name": iface["name"],
                "mode": (iface.get("mode") or "access").lower(),
                "vlan": iface.get("vlan"),
                "allowed_vlans": iface.get("allowed_vlans") or [],
                "description": iface.get("description") or "",
                "enabled": iface.get("enabled", True),
            }
        )

    ntp = device.get("ntp_servers") or ["10.0.0.1"]
    if isinstance(ntp, str):
        ntp = [s.strip() for s in ntp.split(",") if s.strip()]

    return {
        "hostname": device["hostname"],
        "platform": platform,
        "role": device.get("role") or "access",
        "site": device.get("site") or "unknown",
        "mgmt_ip": device.get("mgmt_ip") or "0.0.0.0",
        "mgmt_mask": device.get("mgmt_mask") or "255.255.255.0",
        "default_gateway": device.get("default_gateway") or "",
        "domain_name": device.get("domain_name") or "lab.local",
        "ntp_servers": ntp,
        "snmp_location": device.get("snmp_location") or device.get("site") or "",
        "stp_priority": int(device.get("stp_priority") or 32768),
        "vlans": sorted(vlans, key=lambda v: int(v["id"])),
        "interfaces": interfaces,
        "ansible_host": device.get("ansible_host") or device.get("mgmt_ip") or device["hostname"],
    }


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_device(device: dict[str, Any]) -> str:
    data = normalize_device(device)
    template_name = PLATFORM_TEMPLATE.get(data["platform"])
    if not template_name:
        raise ValueError(f"Unsupported platform: {data['platform']}")
    template = _env().get_template(template_name)
    return template.render(**data)


def write_expected(device: dict[str, Any], content: str) -> Path:
    ensure_dirs()
    data = normalize_device(device)
    path = EXPECTED_DIR / f"{data['hostname']}.cfg"
    path.write_text(content, encoding="utf-8")
    return path


def generate_all(devices: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for device in devices:
        cfg = render_device(device)
        paths.append(write_expected(device, cfg))
    return paths
