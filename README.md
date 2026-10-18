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

`./build.sh` builds with an installed Android SDK and JDK. Public releases are
built and signed in CI.

## Support

Report issues at the [source repository](https://github.com/doccstat/noclearhijack/issues) with
the device model, Android version, Settings package, module version, and reproduction steps.

## Disclaimer

No Clear Hijack changes the Settings **Clear storage** behavior through an
Xposed/LSPosed module. It requires root and is intended for personal use on
devices you own. It is not affiliated with Google, Motorola, LSPosed, or any
device manufacturer. Use it at your own risk: clearing app data is destructive,
and an incompatible framework or firmware update can prevent the device from
booting. The authors are not responsible for data loss, warranty issues, or
problems caused by other modules or firmware.

## License

No Clear Hijack is licensed under the GNU General Public License, version 3 only
(`GPL-3.0-only`). See the
[license text](https://github.com/doccstat/noclearhijack/blob/main/LICENSE).
This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.

## Credits

The `io.github.libxposed.api` interface declarations in `stubs/` mirror the Apache-2.0
[libxposed/api](https://github.com/libxposed/api) 102 surface, and the runtime that loads the
module comes from the user's Xposed framework.
