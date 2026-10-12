# MiniEXE development

MiniEXE is a targeted customization of [Winlator](https://github.com/brunodev85/winlator). The Android app is the upstream `app` submodule plus `patches/miniexe-app.patch`. The original Winlator source, submodule pin, and licenses remain in this repository.

## Build

The [Build MiniEXE APK](.github/workflows/build-miniexe.yml) workflow checks out the pinned app submodule, applies the MiniEXE patch, installs Android SDK 35, NDK 24.0.8215888, and CMake 3.22.1, builds `:app:assembleDebug`, verifies the package ID and ARM64 native library, and uploads the APK for one day. GitHub Actions does not support 12-hour retention, so one day is the shortest requested setting.

For a local build with those SDK components installed:

```sh
git submodule update --init --depth 1 app
git -C app apply ../patches/miniexe-app.patch
cd app
./gradlew :app:assembleDebug
```

The APK is under `app/app/build/outputs/apk/debug/`.

## Current scope

Milestone 1 changes set the Android application ID to `com.miniexe.android`, give the app its own icon and storage path, use Winlator's existing Wine display and Active Windows switcher, and add a hideable quick toolbar and viewport pinch zoom. Run EXE accepts a Windows path in the active container; File Explorer launches Winlator's bundled `wfm.exe` in the same session. Programs installed in the same Wine container can therefore share its display and running session.

The pinned app selects Wine 10.10 and Box64 0.4.4 by default. Its bundled root filesystem contains both `i386-windows` and `x86_64-windows` Wine DLLs, and the launcher uses Box64. This is source and package inspection, not a Pixel 9 execution test. Vortek and Gladio are the selected graphics defaults; Turnip is available for other GPUs but is not required for the defaults.

Physical Pixel 9 behavior, 32-bit WOW64 execution, multitasking behavior, and VEGAS Pro compatibility still require device tests. Optional dependency selection and Simple Mode belong to later milestones.
