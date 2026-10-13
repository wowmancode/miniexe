# MiniEXE development

MiniEXE is a targeted customization of [Winlator](https://github.com/brunodev85/winlator). The Android app is the upstream `app` submodule plus `patches/miniexe-app.patch`. The original Winlator source, submodule pin, and licenses remain in this repository.

## Build

The [Build MiniEXE APK](.github/workflows/build-miniexe.yml) workflow checks out the pinned app submodule, applies the MiniEXE patch, relocates hard-coded app paths in bundled runtime archives, installs Android SDK 35, NDK 24.0.8215888, and CMake 3.22.1, builds `:app:assembleDebug`, verifies the package ID and ARM64 native library, and uploads the APK for one day. GitHub Actions does not support 12-hour retention, so one day is the shortest requested setting.

For a local build with those SDK components installed:

```sh
git submodule update --init --depth 1 app
git -C app apply ../patches/miniexe-app.patch
python3 -m venv .venv
.venv/bin/pip install zstandard==0.25.0
.venv/bin/python scripts/relocate-assets.py app/app/src/main/assets
cd app
bash gradlew :app:assembleDebug
```

The APK is under `app/app/build/outputs/apk/debug/`.

## Current scope

Milestone 1 changes set the Android application ID to `com.miniexes`, give the app its own icon and storage path, use Winlator's existing Wine display and Active Windows switcher, and add a hideable quick toolbar and viewport pinch zoom. The package ID has the same byte length as upstream's because bundled binaries contain absolute app paths that must be rewritten without changing binary layout. Run EXE accepts a Windows path in the active container; File Explorer launches Winlator's bundled `wfm.exe` in the same session. Programs installed in the same Wine container can therefore share its display and running session.

The pinned app selects Wine 10.10 and Box64 0.4.4 by default. Its bundled root filesystem contains both `i386-windows` and `x86_64-windows` Wine DLLs, and the launcher uses Box64. This is source and package inspection, not a Pixel 9 execution test. Vortek and Gladio are the selected graphics defaults; Turnip is available for other GPUs but is not required for the defaults.

Milestone 2 adds a default Simple Mode home screen with Run EXE, installed desktop and Start Menu shortcuts, pinned and recent programs, File Explorer, Running Apps, and Settings. A default container is created when the user first opens the file browser. Settings provides dark and light themes and an Advanced Mode switch; the existing Winlator container and technical controls remain available there. Launching a file or shortcut from the home screen reuses the active Wine session when it belongs to the same container. The Active Windows switcher can minimize and restore windows. Two-finger swipes scroll at normal zoom, while pinch zoom and two-finger panning remain available at higher zoom. The session toolbar has an always-visible Exit button.

Session output is now saved automatically to `/sdcard/Download/MiniEXE/logs.txt` through Android's Downloads API on Android 10 and newer. The file is replaced on each launch. Wine warnings and errors are enabled by default, and an early session exit is reported on the home screen with its exit code. The Logs button in the session toolbar opens the live log.

Physical Pixel 9 behavior, 32-bit WOW64 execution, window interaction, and VEGAS Pro compatibility still require device tests. A reported 32-bit UPX-packed GUI executable briefly shows a black screen and exits; its actual EXE and log have not been supplied, so the cause is unknown. The next diagnostic step is to run it with this build and inspect the saved log. Optional dependency selection is planned for Milestone 3.

## Handoff

The Android source remains pinned as the upstream `app` submodule. Apply `patches/miniexe-app.patch` before editing. Refresh the patch with `git -C app add -N <new files>` and `git -C app diff --binary > patches/miniexe-app.patch`; avoid including relocated runtime archives. CI applies that patch and runs `scripts/relocate-assets.py` before building. Milestone 3 should add optional dependency installation to the shared container while keeping the launch and log paths working.
