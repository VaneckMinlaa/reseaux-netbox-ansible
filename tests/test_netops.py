"""Basic tests for render / validate / drift (no NetBox required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from netops.drift import compare_host, normalize_config_text
from netops.render import generate_all, render_device
from netops.source import load_devices
from netops.validate import validate_devices, validate_rendered_text


def test_load_demo_devices():
    devices = load_devices()
    assert len(devices) >= 3
    assert {d["site"] for d in devices} >= {"pilote", "prod-sim"}


def test_render_cisco_contains_vlans():
    devices = load_devices(hostname_filter="SW-PILOTE-01")
    text = render_device(devices[0])
    assert "hostname SW-PILOTE-01" in text
    assert "vlan 10" in text
    assert "switchport access vlan 10" in text
    assert "{{" not in text


def test_render_arista():
    devices = load_devices(hostname_filter="SW-PILOTE-02")
    text = render_device(devices[0])
    assert "hostname SW-PILOTE-02" in text
    assert "Ethernet24" in text


def test_validate_ok_after_generate(tmp_path, monkeypatch):
    import netops.config as cfg
    import netops.render as render_mod
    import netops.validate as validate_mod

    monkeypatch.setattr(cfg, "EXPECTED_DIR", tmp_path)
    monkeypatch.setattr(render_mod, "EXPECTED_DIR", tmp_path)
    monkeypatch.setattr(validate_mod, "EXPECTED_DIR", tmp_path)

    devices = load_devices(site_filter="pilote")
    generate_all(devices)
    report = validate_devices(devices, expected_dir=tmp_path)
    assert report.ok, [f.message for f in report.errors]


def test_validate_detects_unrendered():
    findings = validate_rendered_text("X", "hostname X\n{{ forgotten }}\n")
    assert any(f.severity == "error" for f in findings)


def test_drift_detects_change(tmp_path):
    exp = tmp_path / "expected"
    run = tmp_path / "running"
    exp.mkdir()
    run.mkdir()
    (exp / "SW.cfg").write_text("hostname SW\nvlan 10\n", encoding="utf-8")
    (run / "SW.cfg").write_text("hostname SW\nvlan 99\n", encoding="utf-8")
    result = compare_host("SW", exp / "SW.cfg", run / "SW.cfg")
    assert result.has_drift


def test_normalize_ignores_noise():
    text = "hostname SW\n! Last configuration change at 1\nvlan 10\n"
    lines = normalize_config_text(text)
    assert lines == ["hostname SW", "vlan 10"]


if __name__ == "__main__":
    # Minimal runner without pytest dependency
    test_load_demo_devices()
    test_render_cisco_contains_vlans()
    test_render_arista()
    findings = validate_rendered_text("X", "hostname X\n{{ forgotten }}\n")
    assert any(f.severity == "error" for f in findings)
    print("smoke tests OK")
