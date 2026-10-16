#!/usr/bin/env python3
"""Direct SDK build for the No Clear Hijack module: no Gradle, no network, no device."""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = Path("META-INF/xposed")


def certificate_digest(value):
    digest = value.replace(":", "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("SIGNING_CERT_SHA256 must be a 64-hex-digit certificate SHA-256 fingerprint")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", action="store_true",
                        help="Require an existing, explicitly configured release signing key")
    args = parser.parse_args()

    if args.release:
        required = ("SIGNING_KEYSTORE", "SIGNING_STORE_PASSWORD", "SIGNING_KEY_PASSWORD",
                    "SIGNING_KEY_ALIAS", "SIGNING_CERT_SHA256")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            parser.error("Release signing requires: " + ", ".join(missing))
        if not Path(os.environ["SIGNING_KEYSTORE"]).is_file():
            parser.error("Release keystore does not exist; refusing to generate a replacement")
        try:
            expected_signer = certificate_digest(os.environ["SIGNING_CERT_SHA256"])
        except ValueError as error:
            parser.error(str(error))

    windows = os.name == "nt"
    sdk = Path(
        os.environ.get(
            "ANDROID_HOME",
            os.environ.get(
                "ANDROID_SDK_ROOT",
                str(Path.home() / ("AppData/Local/Android/Sdk" if windows else "Android/Sdk")),
            ),
        )
    )
    android = Path(os.environ.get("ANDROID_JAR", str(sdk / "platforms/android-36/android.jar")))
    build_tools = Path(os.environ.get("BUILD_TOOLS", str(sdk / "build-tools/36.0.0")))
    java_home = os.environ.get("JAVA_HOME")

    # A throwaway development signer keeps repeated `adb install -r` updates working. Override the
    # paths/credentials for a release; --release refuses to invent a key when one is missing.
    key = Path(
        os.environ.get(
            "SIGNING_KEYSTORE",
            str(Path.home() / (".android/noclearhijack.keystore" if windows
                               else "data/local/noclearhijack/debug.keystore")),
        )
    )
    store_password = os.environ.get("SIGNING_STORE_PASSWORD", "android")
    key_password = os.environ.get("SIGNING_KEY_PASSWORD", store_password)
    key_alias = os.environ.get("SIGNING_KEY_ALIAS", "androiddebugkey")

    env = dict(os.environ, SIGNING_STORE_PASSWORD=store_password, SIGNING_KEY_PASSWORD=key_password)
    if java_home:
        env["PATH"] = str(Path(java_home) / "bin") + os.pathsep + env.get("PATH", "")

    def jtool(name):
        if java_home:
            return Path(java_home) / "bin" / (name + (".exe" if windows else ""))
        found = shutil.which(name)
        if not found:
            raise SystemExit("Set JAVA_HOME to a JDK with " + name)
        return found

    def tool(name):
        override = os.environ.get(name.upper() + "_BIN")
        if override:
            return override
        suffix = ".bat" if name in ("d8", "apksigner") else ".exe"
        return build_tools / (name + (suffix if windows else ""))

    def run(*args):
        subprocess.run([str(x) for x in args], check=True, cwd=ROOT, env=env)

    if not android.is_file():
        raise SystemExit("Set ANDROID_JAR to an SDK platform android.jar")
    if not build_tools.is_dir():
        raise SystemExit("Set BUILD_TOOLS to an SDK build-tools directory")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build.", dir=ROOT) as scratch:
        build = Path(scratch)
        (build / "classes").mkdir()
        (build / "dex").mkdir()
        sources = sorted((ROOT / "src").rglob("*.java")) + sorted((ROOT / "stubs").rglob("*.java"))
        run(
            jtool("javac"), "-source", "8", "-target", "8", "-Xlint:-options",
            "-cp", android, "-d", build / "classes", *sources,
        )
        # Stubs are compile-only; dex just our package so the framework's real API wins at runtime.
        classes = sorted((build / "classes/com/lixingchi").rglob("*.class"))
        run(
            tool("d8"), "--classpath", android, "--classpath", build / "classes",
            "--min-api", "26", "--output", build / "dex", *classes,
        )
        run(tool("aapt2"), "compile", "--dir", ROOT / "res", "-o", build / "resources.zip")
        run(
            tool("aapt2"), "link", "-o", build / "unsigned.apk", "-I", android,
            "--manifest", ROOT / "AndroidManifest.xml", build / "resources.zip",
        )
        with zipfile.ZipFile(build / "unsigned.apk", "a", compression=zipfile.ZIP_DEFLATED) as apk:
            apk.write(build / "dex" / "classes.dex", "classes.dex")
            for name in ("java_init.list", "module.prop", "scope.list"):
                apk.write(str(ROOT / ENTRY / name), "META-INF/xposed/" + name)
        run(tool("zipalign"), "-f", "4", build / "unsigned.apk", build / "aligned.apk")
        if not key.exists():
            if args.release:
                raise RuntimeError("Release keystore disappeared; refusing to generate a replacement")
            key.parent.mkdir(parents=True, exist_ok=True)
            run(
                jtool("keytool"), "-genkeypair", "-keystore", key,
                "-storepass:env", "SIGNING_STORE_PASSWORD",
                "-keypass:env", "SIGNING_KEY_PASSWORD", "-alias", key_alias,
                "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                "-dname", "CN=No Clear Hijack Development,O=NoClearHijack,C=US",
            )
            if not windows:
                key.chmod(0o600)
        output = dist / "NoClearHijack.apk"
        run(
            tool("apksigner"), "sign", "--ks", key, "--ks-pass", "env:SIGNING_STORE_PASSWORD",
            "--key-pass", "env:SIGNING_KEY_PASSWORD", "--ks-key-alias", key_alias,
            "--out", output, build / "aligned.apk",
        )
        verification = subprocess.run(
            [str(tool("apksigner")), "verify", "--verbose", "--print-certs", str(output)],
            check=True, cwd=ROOT, env=env, capture_output=True, text=True,
        )
        print(verification.stdout)
        if args.release:
            digests = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F:]+)",
                                 verification.stdout)
            if len(digests) != 1 or certificate_digest(digests[0]) != expected_signer:
                output.unlink()
                raise RuntimeError("APK signing certificate does not match SIGNING_CERT_SHA256")
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        (dist / (output.name + ".sha256")).write_text(digest + "  " + output.name + "\n",
                                                      encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
