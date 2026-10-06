"""Load device intent from NetBox API or local demo fixtures."""

from __future__ import annotations

from typing import Any

import yaml

from netops.config import DEMO_DATA, NETBOX_TOKEN, NETBOX_URL, SOURCE_MODE


def load_devices(
    site_filter: str | None = None,
    hostname_filter: str | None = None,
) -> list[dict[str, Any]]:
    if SOURCE_MODE == "netbox":
        devices = _from_netbox()
    else:
        devices = _from_demo()

    if site_filter:
        devices = [d for d in devices if d.get("site") == site_filter]
    if hostname_filter:
        devices = [d for d in devices if d.get("hostname") == hostname_filter]
    return devices


def _from_demo() -> list[dict[str, Any]]:
    if not DEMO_DATA.exists():
        raise FileNotFoundError(f"Demo data missing: {DEMO_DATA}")
    with DEMO_DATA.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return list(data.get("devices", []))


def _from_netbox() -> list[dict[str, Any]]:
    if not NETBOX_URL or not NETBOX_TOKEN:
        raise RuntimeError(
            "SOURCE_MODE=netbox requires NETBOX_URL and NETBOX_TOKEN in .env"
        )
    try:
        import pynetbox
    except ImportError as exc:
        raise RuntimeError("Install pynetbox: pip install -r requirements.txt") from exc

    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
    devices_out: list[dict[str, Any]] = []

    for device in nb.dcim.devices.filter(status="active"):
        platform = (device.platform.slug if device.platform else "cisco_ios") or "cisco_ios"
        role = (device.role.slug if device.role else "access") or "access"
        site = (device.site.slug if device.site else "unknown") or "unknown"

        primary_ip = None
        if device.primary_ip:
            primary_ip = str(device.primary_ip.address).split("/")[0]

        # VLANs on site
        vlans = []
        for vlan in nb.ipam.vlans.filter(site_id=device.site.id):
            vlans.append({"id": vlan.vid, "name": vlan.name})

        # Interfaces
        interfaces = []
        for iface in nb.dcim.interfaces.filter(device_id=device.id):
            mode = "access"
            access_vlan = None
            allowed = []
            if getattr(iface, "mode", None):
                mode_val = str(iface.mode.value) if hasattr(iface.mode, "value") else str(iface.mode)
                if "trunk" in mode_val.lower():
                    mode = "trunk"
                elif "access" in mode_val.lower():
                    mode = "access"
            if iface.untagged_vlan:
                access_vlan = iface.untagged_vlan.vid
            if iface.tagged_vlans:
                allowed = [v.vid for v in iface.tagged_vlans]

            # Skip virtual-only noise without description if desired — keep all physical-ish
            interfaces.append(
                {
                    "name": iface.name,
                    "mode": mode,
                    "vlan": access_vlan,
                    "allowed_vlans": allowed,
                    "description": iface.description or "",
                    "enabled": bool(iface.enabled),
                }
            )

        cf = device.custom_fields or {}
        devices_out.append(
            {
                "hostname": device.name,
                "platform": platform.replace("-", "_"),
                "role": role,
                "site": site,
                "mgmt_ip": primary_ip or cf.get("mgmt_ip") or "0.0.0.0",
                "mgmt_mask": cf.get("mgmt_mask", "255.255.255.0"),
                "default_gateway": cf.get("default_gateway", ""),
                "domain_name": cf.get("domain_name", "lab.local"),
                "ntp_servers": cf.get("ntp_servers") or ["10.0.0.1"],
                "snmp_location": cf.get("snmp_location") or site,
                "stp_priority": int(cf.get("stp_priority") or 32768),
                "vlans": vlans,
                "interfaces": interfaces,
                "ansible_host": primary_ip or device.name,
            }
        )
    return devices_out
