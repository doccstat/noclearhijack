# No Clear Hijack

An Xposed module for Android that stops the Settings **Clear storage** button from being
redirected into an app's own "manage space" screen.

## What it fixes

Android lets an app declare `android:manageSpaceActivity` in its manifest. When it does, AOSP
Settings still shows the **Clear storage** button on *App info → Storage & cache*, but tapping it
launches the app's `manageSpaceActivity` instead of clearing data. The app then decides what (if
anything) to delete, so the user cannot trust the button.

No Clear Hijack clears that redirection inside the Settings process, so the button always opens the
normal clear-data confirmation and calls `ActivityManager.clearApplicationUserData`. It applies to
every app that declares a manage-space activity.

It does **not** bypass device administrator or `DISALLOW_APPS_CONTROL` restrictions; those remain
deliberate device-management controls.

## Requirements

- Android 8.0 (API 26) or newer.
- A modern Xposed framework that supports the libxposed API 102, such as LSPosed or Vector.
- Module scope: `com.android.settings` (declared in the APK).

## Install

1. Install the latest APK from [Releases](https://github.com/doccstat/noclearhijack/releases)
   (or build it yourself; see *Build* below).
2. Enable the module in the Xposed manager and confirm its scope contains `com.android.settings`.
3. Force-stop Settings (or reboot) so the hook is injected.

Reinstalling a module (uninstall + install) resets the manager's enabled/scope state, so re-enable
it and re-add the `com.android.settings` scope after a clean install. Published releases are signed
with a permanent key, so later versions install over earlier ones normally.

## Build

Requires an Android SDK (one platform plus build-tools) and a JDK 8 or newer:

```shell
export ANDROID_HOME=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk
./build.sh
```

`build.py` compiles the Java sources against the compile-only API stubs in `stubs/`, packages the
libxposed entry/metadata files, and signs the result. The first build creates a development
keystore; keep it if you want later builds to install over earlier ones.

The module is built against libxposed API 102 and declares `targetApiVersion=102`. CI builds the
public releases with `python3 build.py --release`, which requires an existing release keystore and
the `SIGNING_KEYSTORE`, `SIGNING_STORE_PASSWORD`, `SIGNING_KEY_PASSWORD`, `SIGNING_KEY_ALIAS`, and
`SIGNING_CERT_SHA256` environment variables and refuses to generate a key.

## Layout

- `src/` — module code.
- `stubs/` — compile-only libxposed API declarations; never packaged into the APK.
- `META-INF/xposed/` — entry list, module properties, and scope.
- `build.py` / `build.sh` — direct SDK build.
- `tests/` — package metadata and release-signing guard checks.
- `.github/workflows/` — build, signed release, and LSPosed listing distribution.
- `SUMMARY` — one-line LSPosed listing description.

## Support

Report issues at the [source repository](https://github.com/doccstat/noclearhijack/issues) with
the device model, Android version, Settings package, module version, and reproduction steps. This
project is not affiliated with Google, Motorola, or LSPosed.

## Credits

The `io.github.libxposed.api` interface declarations in `stubs/` mirror the Apache-2.0
[libxposed/api](https://github.com/libxposed/api) 102 surface, and the runtime that loads the
module comes from the user's Xposed framework.
