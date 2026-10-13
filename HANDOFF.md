# MiniEXE technical handoff

Last updated: 2026-10-12. This document describes the Android implementation at commit
`256e56bc74b89bb15247ff3018e4e693bd7b64c1` on `main`.

## Project and repository

- MiniEXE repository: <https://github.com/wowmancode/miniexe>
- Winlator upstream: <https://github.com/brunodev85/winlator>
- Goal: a Winlator-based Android EXE runner for ARM64 phones, with the Google
  Pixel 9 as the target device. Preserve Winlator's Wine, Box64, graphics,
  audio, input, container, file, and window systems.
- Android application ID: `com.miniexes`. The visible name and icon are
  MiniEXE. The Java namespace remains `com.winlator` because a namespace
  rewrite is unnecessary for side-by-side installation.
- The `app` submodule is pinned to Winlator app commit
  `a030f552f452158a2db64fdb32b490fa19c0b48d`. Do not update that pin as
  part of an unrelated change. The root `vortek` and `gladio` submodules are
  currently uninitialized; the existing APK workflow initializes `app` only.
- Upstream attribution and the root and app `LICENSE` files remain present.

The Android source is **not copied into the root repository**. CI checks out
the pinned `app` submodule, applies [`patches/miniexe-app.patch`](patches/miniexe-app.patch),
rewrites the bundled runtime paths with [`scripts/relocate-assets.py`](scripts/relocate-assets.py),
then builds the APK. A clean local checkout of `app` therefore looks like
Winlator until the patch is applied.

## Delivered milestones

### Milestone 1: first APK candidate

- Separate package ID, app label, icon, app data path, FileProvider authority,
  service identifiers, and native hard-coded paths.
- Wine desktop shell is hidden while applications run in the existing hosted
  display. The Active Windows dialog and Wine window management remain in use.
- A compact, hideable in-session toolbar initially provided Run EXE,
  fullscreen, keyboard, reset zoom, Wine File Explorer, and Running Apps.
- Direct touch is the default. Pinch magnifies the rendered view, and zoom is
  remembered. Existing trackpad and external mouse/keyboard paths remain.

### Milestone 2: UI, scrolling, and diagnostics

- Simple Mode is the default home screen. It offers Run EXE, Installed
  Programs, Recent Applications, pinned programs, Running Apps, File Explorer,
  and Settings. Long-press a recent item to pin it; long-press a pinned item
  to remove it.
- The first file-browser opening creates one default Wine container when none
  exists. The home browser uses Winlator's container file manager, including
  its C: drive and configured Android drives. The in-session File Explorer
  button launches Wine's `wfm.exe`.
- Installed Programs lists Winlator desktop shortcuts and Wine Start Menu
  `.lnk` entries. It is limited to applications with discoverable shortcuts.
- Launches from the file manager, shortcuts, and home screen reuse the active
  Wine session when the container matches. A different container requires the
  current session to be closed first. Running Apps returns to the active
  session and opens Winlator's window list. The list now has minimize and
  restore actions; window titles and icons come from Winlator's X window data.
- Two-finger movement scrolls at normal zoom. Pinch still zooms; at increased
  zoom, two-finger movement pans the viewport. The session Exit button remains
  visible when the toolbar is collapsed. Home and Logs were added to that
  toolbar in this milestone.
- Simple Settings offers dark/light themes and Advanced Mode. Advanced Mode
  exposes the existing Winlator container, input, and technical settings.
- Launch output is saved automatically to
  `/sdcard/Download/MiniEXE/logs.txt`. Android 10+ uses the Downloads
  MediaStore API; older Android uses the filesystem path. The file is replaced
  at each new session. Wine error and warning channels are enabled by default.
  Early session exits are shown on the home screen with their exit code; the
  Logs button opens the live log. Existing MiniEXE settings cannot disable
  this diagnostic log.

### Milestone 2.1: home-screen container settings

- The Simple Mode home screen has a **Container** section showing the home
  container's name, screen size, graphics driver, DX wrapper, and Box64
  preset, plus a note when that container is the one currently running
  (changes apply after the session is closed).
- **Container Settings** opens Winlator's full container editor
  (`ContainerDetailFragment`) for the home container, creating the default
  container first if none exists. Advanced Mode is no longer required to
  change per-container settings.
- With more than one container, **Switch Container** picks which one the home
  screen targets. The choice is stored in the `miniexe_home_container`
  preference and is also used by Run EXE and File Explorer. A deleted
  selection falls back to the first container.
- Code: `MainActivity.getHomeContainer/withHomeContainer/openContainerSettings`,
  `MiniHomeFragment.addContainerSection`, and
  `XServerDisplayActivity.getActiveContainerId`.

CI build for this change passed:
<https://github.com/wowmancode/miniexe/actions/runs/38328736344> (APK built and
checked; no device test yet).

### Milestone 3: optional dependency installer (built, not device-tested)

- **Entry points.** On first launch, once the runtime is installed, the home
  screen opens **Dependencies** once (`miniexe_deps_prompted`); **Skip**
  leaves the container untouched. It is also reachable from the home screen
  and Settings at any time.
- **Catalog.** `app/src/main/assets/miniexe/dependencies.json` lists every
  item, its category, downloads (URL, pinned SHA-256, file name), install
  commands, DLL overrides, Windows-version override, requirements, conflicts,
  and how it is verified. URLs and hashes come from Wine 10.10's
  `appwiz.cpl/addons.c` (Wine Mono) and winetricks `20260125-next`. The 11
  corefonts hashes were also checked by downloading them.
- **Bundled items (no download).** Winlator's existing wincomponents
  (D3DX/D3DCompiler, DirectSound, DirectMusic, XAudio, DirectPlay,
  DirectShow, WM decoders, VC++ 2005, VC++ 2010) are toggled per container
  and applied by Winlator at the next session start.
- **Downloaded installers.** Wine Mono 10.1.0; .NET 3.5 SP1, 4.0, 4.5; VC++
  2008, 2012, 2013, 2015–2022; corefonts; MSXML 3; MSXML 6 SP2. Files are
  cached in `files/miniexe/dependency-cache` (cleared from the screen) and
  exposed to Wine as `C:\miniexe\cache` through a symlink. A SHA-256
  mismatch discards the file and reports an error. Sizes come from HTTP HEAD
  requests when the server reports them.
- **Install.** `DependencyManager.writeInstallScript` writes
  `C:\miniexe\install.bat`, run in the container's open session or a new
  one. It sets DLL overrides and a temporary `HKCU\Software\Wine\Version`
  where winetricks does (.NET 4.0 → winxp, 4.5 → win7), runs each
  installer with `start /wait`, records exit codes in
  `C:\miniexe\status\<id>.txt` and `C:\miniexe\install-log.txt`, and
  opens the log in Notepad. Font and MSXML 6 packages are self-extracting
  cabinets: the app copies out the embedded cabinet and Wine's `extrac32`
  unpacks it (no cabextract in the rootfs).
- **Verified status.** Shown status is read from the container, not from
  the script: native (non-Wine-builtin) DLLs in `system32`/`syswow64`,
  expected files, `NET Framework Setup` registry values in `system.reg`, or
  uninstall display names. A failed attempt shows its exit code.
- **Conflicts.** Selecting .NET deselects Wine Mono and removes an installed
  Wine Mono first (via its cached MSI). .NET 4.5 requires and replaces 4.0.
  GDI/GDI+ and Direct3D 10–12 rendering are listed as information only
  (Wine builtins and the container DX wrapper).
- **Code:** `DependencyManager.java`, `DependenciesFragment.java`, the
  catalog asset, and small hooks in `MiniHomeFragment` and
  `MiniSettingsFragment`.

First device report (2026-10-12): VC++ 2012 exited 0; .NET 4.0 never
started. Wine's `start.exe` failed before the installer process existed (no
`init_peb` line in the log). Two deviations from winetricks were fixed: the
temporary Windows version is now `winxp64` (winetricks' choice for 64-bit
prefixes) instead of `winxp`, and installers are now run directly from the
batch file rather than via `start /wait`. Wine's `cmd` waits for GUI
programs in batch mode and passes the original command line, which preserves
`/c:"install.exe /q"`. The install log now records each command line and its
exit code. Re-test .NET 4.0 after this build.

Second report: an install finished with exit code 6, which has no
documented meaning for .NET 4 setup. The script now copies installer logs
(`%TEMP%\dd_*.*`, `*.htm*`, `*.log`) and `install-log.txt` to
`C:\miniexe\setup-logs` and, when drive D: (the default Downloads mapping)
exists, to `Download/MiniEXE/setup-logs`. A progress panel
(`widget/DependencyProgressOverlay.java`) now shows in the session while
the script runs: it polls `C:\miniexe\progress.txt` (`STEP i n name`, then
`DONE n`), with an overall per-item bar and an indeterminate bar for the
current installer, since installers report no percentage.

Third report: run directly from the batch file, the .NET 4.0 line still
returned 6 and `logs.txt` again had no `init_peb` line for it, so Wine's
`cmd` could not create the process at all (`CreateProcess`/`ShellExecuteEx`
failed with ERROR_INVALID_HANDLE); the installer itself never ran. VC++
installers from the same cache directory start normally. .NET items now run
each installer from a nested `cmd` with `WINEDEBUG=+process,+module,+loaddll,+seh`
added (trace goes to `Download/MiniEXE/logs.txt`), and items with a Windows
version override retry once without it if they fail. Next step: read that
trace to see why process creation fails before changing the approach.

Fourth report: the retry without the Windows version override failed the
same way (code 6), so the version override is not the cause. The trace
shows `NtCreateUserProcess` for `dotNetFx40_Full_x86_x64.exe` failing
before any child process exists. The retry was removed. The .NET 4.0/4.5
first attempt now traces with `+process,+server`, so the wineserver reply
that rejects the launch is visible in `logs.txt`. If the self-extractor
cannot be started, a fallback copies out its embedded cabinet on the
Android side (`tryExtractCab`, `prepareCabs`), unpacks it with `extrac32`,
and runs the extracted `install.exe` or `Setup.exe` silently.

Fifth report (wineserver trace, 2026-10-13): `new_process` for the .NET 4.0
self-extractor succeeds (i386, pid assigned), but its first thread is killed
with exit code 1 before it sends any request (no `get_startup_info`), i.e.
the child dies inside the Unix-side Wine/Box64 startup before any Windows
code runs. VC++ i386 installers pass the same point. The fallback ran, but
`extrac32` reported "Could not extract cab file" for the first embedded
cabinet. Changes: the app now copies out every embedded cabinet into
`<download>.cabs/` (spanned members named as their headers expect) and
logs each header (size, files, flags, compression, prev/next) to
`install-log.txt`; the fallback unpacks each root cabinet and lists the
extracted files. The first attempt now runs with `BOX64_LOG=1`,
`BOX64_SHOWSEGV=1`, `BOX64_DLSYM_ERROR=1` and `WINEDEBUG=+process,+virtual`
(no `+server`, which produced 24 MB) to capture why the child exits.

Sixth report: with `BOX64_LOG=1` the .NET child still printed nothing, so
the failure is probably in the fork/exec step (Wine's spawn child `_exit(1)`s
silently when exec fails) rather than inside Box64. Not yet confirmed.
Wine's Notepad cannot copy to the Android clipboard, so the install log is
now exported by the app to `Download/MiniEXE/install-log.txt` when the
script reports DONE, and Dependencies has "View last install log" with
Copy (Android clipboard) and Share. `LogView.openDownloadsFile` generalises
the MediaStore writer.

Seventh report: the fallback found 0 valid cabinets in
`dotNetFx40_Full_x86_x64.exe` (the cabinet found earlier was a false match
that `extrac32` rejected), so the .NET 4 payload is not a plain embedded
MSCF cabinet. The install log now includes the PE header (machine, flags,
image base/size, relocations, CLR and certificate sizes) and section table
of the installer, plus every raw `MSCF` signature with its header fields, to
identify the real container format. Cabinet output moved to `.cabs2/` so
the rescan is not skipped.

Eighth report: the .NET 4.0 installer is a small (213 KB image, base
0x400000, relocatable, 32-bit) Microsoft "box" stub (`.boxld01` section)
followed by a ~50 MB overlay with no MSCF signature, so its payload can
only be unpacked by the stub itself. Wine's `spawn_process` grandchild
`_exit(1)`s silently if `exec` of the loader fails, and argv is rebuilt
from the Windows command line; the only difference from the working VC++
launches is the quoted `/c:"install.exe /q"` argument (an IExpress-era
winetricks switch). .NET 4.0/4.5 now run with their native `/q /norestart`,
with fallback `/x:<tmp> /q` extraction and the extracted `Setup.exe /q
/norestart`.

Ninth report: `/q /norestart` and `/x:<dir> /q` fail identically (code 6,
no child startup), so the quoted argument was not the cause; Wine cannot
start this stub with any arguments. The fallback now runs three probes:
(A) a copy stored inside the prefix instead of behind the cache symlink,
(B) a 512 KB truncated copy without the payload (`<file>.probe.exe`,
started with `start` so an error dialog cannot block), and (C) `/x`
self-extraction. Whether B starts (an `init_peb` line in `logs.txt`) shows
whether the 50 MB overlay is what prevents process creation.

Tenth report: with the probe build the .NET installer appeared to start
and kept running (no completion yet), so a launch path now works; which
attempt succeeded is not yet confirmed from logs. Installers now run in
their own progress-UI modes (`/passive` for .NET 4.x and VC++ 2012–2022,
`/qb` for VC++ 2008 and MSI packages), which is the only real percentage
available since installers expose none externally. The install panel
shows elapsed time per item and a Processes button; the session toolbar
also has Processes. Both open Winlator's existing `TaskManagerDialog`
(process list with memory and end-task, per-core CPU usage, memory,
battery). The truncated-stub probe was removed; the fallback keeps the
in-prefix copy and `/x` extraction.

Eleventh report — **.NET 4.0 installed.** The fallback's copy of the
installer stored inside drive C: ran to completion (extracted `Setup.exe`,
`msiexec`, `lodctr`, `regtlibv12`, `ngen`/`mscorsvw`), while the identical
file reached through `C:\miniexe\cache` (a symlink to
`files/miniexe/dependency-cache`, outside the rootfs) never starts.
Root cause of that difference is not established; VC++ installers do start
through the symlink. Every install now copies the item's cached files to
`C:\miniexe\stage\<id>` first, runs from there, and removes the copy.
The .NET probes, fallback and diagnostic tracing were removed.

**Root cause found (twelfth report).** Staging alone did not help: the
staged `dotNetFx40_Full_x86_x64.exe` failed again while `setupcopy.exe`
had worked. Winlator's `assets/box64/default.box64rc` contains
`BOX64_EXIT=1` rules for `[*dotnetfx*]`, `[*ndp452-kb*]`, `[*ndp462-kb*]`,
`[*ndp472-kb*]` and `[*ndp48-x86-x64*]`, so Box64 kills those processes by
name before Wine starts — the silent exit 1 seen in every trace. The cache
symlink was not the cause. Catalog downloads can now set `stageAs`; the
.NET 3.5/4.0/4.5 installers are staged as `netfx35setup.exe`,
`netfx40setup.exe` and `netfx45setup.exe`. The upstream rule is kept, so
user-launched installers with those names are still blocked; consider
surfacing that (or removing the rule) after testing .NET under Box64.

**Thirteenth report — rename confirmed.** `netfx40setup.exe` started and
ran the full .NET 4.0 sequence (extracted `Setup.exe`, `msiexec`,
`lodctr`/`unlodctr`, `regtlibv12`, `mofcomp`, `ngen` with 18 `mscorsvw`
runs, then a second `msiexec` for the Extended package). The session was
then SIGKILLed (`Guest process exited with code 137`, Exit button or
Android) during the second `msiexec`, so the script never reached DONE and
the Downloads `install-log.txt` was the previous run's. Exit now asks for
confirmation while `DependencyManager.isInstallRunning()`. A complete,
uninterrupted .NET 4.0 install and its verified status are still pending.

**Windows version.** Wine uses HKCU\Software\Wine "Version" (winecfg)
when present and only otherwise the HKLM NT CurrentVersion keys (what
Winlator's container setting writes), and registry files edited while a
container runs are overwritten by wineserver on exit. The install script
previously *deleted* the "Version" value after .NET items, wiping winecfg
choices; it now restores the value it found. `WindowsVersion.java` sets
both places (directly when stopped, via a `reg.exe` batch inside the
session when running), the home screen shows "Windows version: …" with a
picker, and Winlator's container editor now uses the same code.

**Releases:** each push to `main` replaces the single GitHub release
`latest` (tag and release deleted, then recreated at the new commit) with
`MiniEXE-arm64-debug.apk`; stable link:
<https://github.com/wowmancode/miniexe/releases/latest/download/MiniEXE-arm64-debug.apk>.
Actions artifact uploads were removed.

Not yet established on a device: each installer's silent switches under
Wine 10.10 + Box64, .NET installs in general (historically fragile under
Wine), whether `aka.ms` VC++ 2015–2022 hashes still match (Microsoft
replaces that file in place), and extrac32/LZX behaviour for the font
cabinets. The pure-Java cabinet, registry and builtin-DLL checks were
unit-tested off-device. CI build for this milestone passed:
<https://github.com/wowmancode/miniexe/actions/runs/38330298895>.

### 32-bit programs

32-bit Windows EXEs run through Wine WOW64 on Box64; box86 is not needed and
is not planned. Many 32-bit programs need x86 runtimes, which Milestone 3
installs (both x86 and x64 VC++ packages are run).

### Box86: requested, not added

Box86 was requested in the same change and deliberately not implemented:

- Box86 is an armhf (32-bit ARM) binary. The Pixel 9's Tensor G4 CPU cores
  (Cortex-X4, A720, A520) are AArch64-only, so a box86 binary cannot execute
  on the target device.
- The pinned Winlator runtime has no armhf userspace and uses a WOW64 Wine
  build; box86 would also need a separate 32-bit ARM rootfs and a non-WOW64
  i386 Wine build, which upstream Winlator removed.
- 32-bit Windows programs already run through Wine WOW64 under Box64; the
  per-container Box64 preset is now reachable from the home screen.

If box86 is wanted for other, AArch32-capable devices, scope it as a separate
optional runtime with its own rootfs and Wine build, and keep it off by
default on AArch64-only CPUs.

The implementation details and short build instructions are also in
[`MINIEXE.md`](MINIEXE.md).

## Build and verification status

The latest GitHub Actions run is
<https://github.com/wowmancode/miniexe/actions/runs/38327425320> at commit
`256e56b`. It completed successfully and uploaded the
`MiniEXE-arm64-debug` artifact, ID `11781865983` (about 188 MB compressed).
The artifact expires on 2026-10-14 at 00:31:43 UTC; source code and build
instructions remain in the repository. The workflow is configured for one-day
retention because 12 hours is not supported by `upload-artifact`.

The CI workflow verifies that the APK exists, is nonempty, has Android package
`com.miniexes`, and contains `lib/arm64-v8a/libwinlator.so` before upload. A
local full `:app:assembleDebug` build passed for Milestone 2, and a local Java
compile passed after the final logging adjustment. These results establish
buildability, **not** successful Windows execution on a phone.

### Local build requirements

- JDK 17
- Android SDK platform 35 and build tools 35.0.0
- Android NDK 24.0.8215888 and CMake 3.22.1
- Python with `zstandard==0.25.0`
- Gradle wrapper and the dependency downloads specified by the pinned app

From a clean repository checkout:

```sh
git submodule update --init --depth 1 app
git -C app apply --check ../patches/miniexe-app.patch
git -C app apply ../patches/miniexe-app.patch
python3 -m venv .venv
.venv/bin/pip install zstandard==0.25.0
.venv/bin/python scripts/relocate-assets.py app/app/src/main/assets
cd app
./gradlew :app:assembleDebug --no-daemon --max-workers=2 \
  -Dorg.gradle.jvmargs='-Xmx3g -XX:MaxMetaspaceSize=768m'
```

Set `ANDROID_HOME` to the installed SDK first. The APK is produced at
`app/app/build/outputs/apk/debug/app-debug.apk` relative to the root
repository. The [GitHub Actions workflow](.github/workflows/build-miniexe.yml)
is the repeatable reference build, including SDK installation and artifact
checks.

### Working on the app patch

1. Start with a clean `app` submodule at the pinned commit, and apply the
   current patch once.
2. Edit files under `app/app/`. For any new files, run `git -C app add -N`
   with their paths relative to the submodule.
3. Refresh the root patch with
   `git -C app diff --binary > patches/miniexe-app.patch` and run
   `git -C app diff --check`.
4. Check patch application against a clean pinned submodule before pushing.
   Commit the updated **root patch**, documentation, and workflow as needed.
5. Run runtime archive relocation **after** generating the patch. The script
   rewrites large bundled `.tzst` assets in place; do not include those
   generated binary changes in the patch. Restore those asset files before
   regenerating a patch or cleaning the submodule.

`com.miniexes` was chosen because it has the same byte length as upstream's
`com.winlator`. The bundled archives contain absolute app paths, including
paths inside ELF content. The relocation script replaces ASCII and UTF-16LE
references without changing the embedded path length. If the package ID is
changed again, review this constraint and every package-dependent reference.

### Code locations after applying the patch

All Android paths below are relative to the `app` submodule:

| File or area | Responsibility |
| --- | --- |
| `app/src/main/java/com/winlator/MainActivity.java` | Main navigation, default container/browser launch, recent program records |
| `app/src/main/java/com/winlator/MiniHomeFragment.java` | Simple Mode actions, container summary/settings/switcher, recent and pinned programs |
| `app/src/main/java/com/winlator/InstalledProgramsFragment.java` | Desktop and Start Menu shortcuts |
| `app/src/main/java/com/winlator/MiniSettingsFragment.java` | Theme and Advanced Mode entry |
| `app/src/main/java/com/winlator/XServerDisplayActivity.java` | Wine session lifecycle, toolbar, same-session launch, early-exit reporting |
| `app/src/main/java/com/winlator/widget/TouchpadView.java` and `renderer/GLRenderer.java` | Scroll, touch, zoom, and rendered-view panning |
| `app/src/main/java/com/winlator/contentdialog/ActiveWindowsDialog.java` | Window switcher and minimize/restore |
| `app/src/main/java/com/winlator/widget/LogView.java` and `core/ProcessHelper.java` | Downloads log and guest output capture |
| `app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java` | Box64 guest launch and background behavior |
| `app/src/main/AndroidManifest.xml`, `app/build.gradle`, native renderer headers, and resources | Package identity and rebranding |

## Engine and feature map

| Area | Current implementation | Evidence and limit |
| --- | --- | --- |
| Windows runtime | Pinned Winlator root filesystem and Wine 10.10 | Source and archive inspection; no Pixel 9 launch test |
| CPU translation | Box64 0.4.4 launcher | Launcher source and bundled asset; no device execution test |
| 32-bit Windows path | Wine WOW64 files for `i386-windows` and `syswow64` | Bundled files inspected; PE32 execution unverified |
| 64-bit Windows path | Wine files for `x86_64-windows` | Bundled files inspected; PE64 execution unverified |
| Graphics | Vortek and Gladio defaults, with other Winlator options in Advanced Mode | Selected defaults do not require Turnip/Adreno; Pixel 9 Mali behavior unverified |
| Audio and input | Existing Winlator systems plus MiniEXE touch gestures | Source inspection and APK build; device behavior unverified |
| Windows and multitasking | One active container/session, Wine windows, Active Windows switcher | Static active-session routing and `singleTask` activity need device testing |
| File access | Winlator container drives and file manager | Android folder permissions depend on the existing Winlator implementation |
| Logs | Downloads MediaStore/file output | Compiled and built; actual Downloads write needs device verification |

The Android app targets SDK 28 in the pinned source and builds with SDK 35.
This is inherited from Winlator. The APK is an ARM64 build. It does not need
root or a Windows ISO, but Windows program licensing still applies.

## Known issues and risks

1. A user-reported **PE32 i386 GUI executable compressed with UPX** opens a
   black screen briefly and exits. Its program name, binary, and MiniEXE log
   have not been provided. The `file` output alone cannot distinguish a Wine,
   Box64/WOW64, dependency, graphics, or application failure. Do not claim a
   fix yet. Reproduce on the Pixel 9, copy the log before another launch
   replaces it, and investigate the first relevant error and exit status.
2. No physical Pixel 9 test has established x86, x64, installers, command-line
   programs, multiple windows, background behavior, touch gestures, or
   Downloads log writes. CI success must not be reported as device support.
3. Simple Mode's Run EXE opens the container file browser; it is not an Android
   system document picker. Installed Programs depends on desktop or Start Menu
   shortcuts being present. The window list has minimize/restore and switching;
   normal Wine window controls handle per-window close.
4. The active session uses an Android activity and background process behavior
   from Winlator, with a MiniEXE change that keeps the guest process running
   when switching to the home screen. Validate this against Android resource
   limits and lifecycle events before promising persistent background work.
5. Logs can include local file paths and application diagnostics. Ask the user
   to review the file before posting it publicly. The current file is
   overwritten on each session; copy it before testing another EXE.
6. The basic installed storage target of 1–3 GB has not been measured on a
   Pixel 9. Optional dependencies and their storage use are not implemented.

## Suggested device test order

1. Install original Winlator and MiniEXE side by side; confirm separate data,
   settings, icons, and no change to existing Winlator containers.
2. Start MiniEXE, create the default container through Run EXE, and launch
   known-good 32-bit and 64-bit console and GUI test programs. Record each
   binary's architecture and exact Wine/Box64 configuration.
3. Run an installer, relaunch its installed shortcut, and confirm persistence
   after closing and reopening MiniEXE.
4. Open two Windows applications in one container, switch, move, resize,
   minimize, restore, close, and launch another EXE while one is active.
5. Test two-finger scrolling, pinch, zoomed panning, direct touch, trackpad,
   keyboard, mouse, fullscreen, and Exit. Test leaving and returning to Home.
6. Verify `Download/MiniEXE/logs.txt` is created, readable, and replaced on a
   new session. Then reproduce the reported UPX program and preserve its log.
7. Test Mali graphics with the defaults and a software/OpenGL fallback before
   changing any backend globally. Keep per-container settings available.

## Remaining development milestones

### Milestone 3: optional dependencies — implemented (see above); device validation remaining

Original scope: build a first-run **optional** dependency picker and later Settings access.
Users must be able to Skip and run simple EXEs. The requested choices are
.NET 3.5 SP1, 4.0, 4.5, Wine Mono; vcrun2005 through vcrun2019; DirectX 9
and supported 10/11 compatibility; corefonts; MSXML 3/6; GDI/GDI+; and
practical DirectShow/legacy media components. Show download/install sizes
when known, progress, errors, cached installers, and **verified** installed
status. Handle .NET 4.5 replacing 4.0 in one prefix, runtime conflicts, and
separate prefixes when needed. Use legitimate downloads and obey Microsoft
redistribution restrictions. Reuse Winlator component installation or
Winetricks-compatible paths where practical. Do not add a fake installer UI.

### Milestone 4: application compatibility

Test multiple x86 and x64 applications on hardware. Investigate VEGAS Pro
**13 first**, then 11, 12, 14, and 15. Record installer, launch, editor,
timeline, imports, preview, audio, export, and licensing outcomes. Fix
demonstrated problems where practical; document Wine, graphics, media, or
licensing blockers. Never bypass activation or claim compatibility without
actual tests.

### Milestone 5: final validation

Resolve major regressions, verify installation and actual device behavior,
document supported features and limits, and publish durable final artifacts.
Retain the side-by-side package identity and upstream notices. For each
milestone, commit the work, report relevant files and build results, list
remaining issues, and update this handoff.

## Immediate next action for another developer or AI

Obtain the failing program's `/sdcard/Download/MiniEXE/logs.txt` from the
latest APK and reproduce it on the Pixel 9. Capture the EXE name/version and
whether the failure occurs on first launch or only after an installer. If the
log shows a missing runtime or DLL (for example `msvcr*`, `msvcp*`,
`mscoree`, or `d3dx9_*`), install it from Dependencies and re-test. Then run
the Milestone 3 device checks: install each dependency on the Pixel 9 and
confirm the Dependencies screen reports it as verified.
