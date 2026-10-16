#!/usr/bin/env python3
"""Static package checks for No Clear Hijack. No Android SDK, JDK, or device required."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XPOSED = ROOT / "META-INF" / "xposed"


def test_entry_class_exists():
    entries = [line.strip() for line in (XPOSED / "java_init.list").read_text().splitlines()]
    assert entries == ["com.lixingchi.noclearhijack.NoClearHijack"], entries
    source = ROOT / "src" / Path(*entries[0].split(".")).with_suffix(".java")
    assert source.is_file(), source
    assert f"class {entries[0].rsplit('.', 1)[1]}" in source.read_text()


def test_scope_is_settings_only():
    scope = [line.strip() for line in (XPOSED / "scope.list").read_text().splitlines()]
    assert scope == ["com.android.settings"], scope


def test_module_prop_api():
    props = dict(
        line.split("=", 1) for line in (XPOSED / "module.prop").read_text().splitlines() if line
    )
    assert props["minApiVersion"] == "102", props
    assert props["targetApiVersion"] == "102", props


def test_manifest_has_package():
    manifest = (ROOT / "AndroidManifest.xml").read_text()
    assert 'package="com.lixingchi.noclearhijack"' in manifest
    assert "@string/app_name" in manifest


def test_stub_is_compile_only():
    build = (ROOT / "build.py").read_text()
    # Only our package may be dexed; stubs must stay out of the APK.
    assert 'build / "classes/com/lixingchi"' in build
    assert "io/github/libxposed" not in build


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)
