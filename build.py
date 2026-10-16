#!/usr/bin/env python3
"""Direct SDK build for the No Clear Hijack module: no Gradle, no network, no device."""
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENTRY = Path("META-INF/xposed")


def main():
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
    env = dict(os.environ)
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

    # A throwaway development signer so repeated `adb install -r` updates keep working. Override
    # with SIGNING_KEYSTORE for a release build; back the generated file up before publishing.
    keystore = Path(
        os.environ.get(
            "SIGNING_KEYSTORE",
            str(Path.home() / (".android/noclearhijack.keystore" if windows
                               else "data/local/noclearhijack/debug.keystore")),
        )
    )

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
        if not keystore.exists():
            keystore.parent.mkdir(parents=True, exist_ok=True)
            run(
                jtool("keytool"), "-genkeypair", "-keystore", keystore, "-storepass", "android",
                "-keypass", "android", "-alias", "androiddebugkey", "-keyalg", "RSA",
                "-keysize", "2048", "-validity", "10000",
                "-dname", "CN=No Clear Hijack Development,O=NoClearHijack,C=US",
            )
            if not windows:
                keystore.chmod(0o600)
        output = dist / "NoClearHijack.apk"
        run(
            tool("apksigner"), "sign", "--ks", keystore, "--ks-pass", "pass:android",
            "--key-pass", "pass:android", "--ks-key-alias", "androiddebugkey",
            "--out", output, build / "aligned.apk",
        )
        run(tool("apksigner"), "verify", "--verbose", output)
        print(output)


if __name__ == "__main__":
    main()
