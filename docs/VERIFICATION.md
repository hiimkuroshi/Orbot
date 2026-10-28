# Verification · Orbot 0.2.1 security update · 28 October 2026

Local checks (Linux sandbox; Python 3.14.10; Tk 8.6 on Xvfb, Inter substituted for Segoe UI):

- Reproduced before the fix: any local process could read a page secret through an unauthenticated Chromium DevTools port, while a WebSocket with a web `Origin` was rejected (403). Also reproduced: a CDP error sent as text killed the worker thread, after which Orbot could not close normally.
- Node engine suite: 29 passed. Python suite: 23 tests, 21 passed and 2 Windows-only tests skipped locally (they read the real Windows TCP table and run in CI).
- New tests cover malformed CDP replies, the worker surviving unexpected errors, owner checks (Discord accepted; other, mixed, unknown and missing listeners refused; no HTTP request before the check), port classification, port settings and random port selection.
- GUI smoke passed on real Tk widgets, including the footer port note and the close reminder (shown only while the port is open; Quay lại keeps Orbot open). Previews of the connection dialog, close reminder and connected footer were inspected at 96 DPI.
- Ruff, Mypy (Linux and `--platform win32`), Bandit (no medium/high), pip-audit on requirements-lock.txt (no known vulnerabilities) and actionlint passed. PyInstaller parsed the generated version resource.

Not verified: the random port and owner check against a real Discord Desktop, the SmartScreen result of the new build, and Microsoft or SignPath submissions (manual steps in PUBLISHING.md). No Quest was run or claimed.

---

# Verification · Orbot 0.2.0 Focus Flow · 26 October 2026

GitHub release verification, 26 October 2026:

- Preserved the existing GitHub initial commit and MIT license. Source, documentation and assets are tracked; .venv/, dist/ and build/ remain ignored.
- Re-ran scripts/verify.ps1: 29 engine tests, 7 local HTTP/WebSocket tests, real Tk GUI smoke, Ruff, Mypy and medium/high Bandit checks passed. The loopback suite required execution outside the socket-restricted sandbox.
- Rebuilt the Windows x64 one-file EXE from the current source. The build now bundles the project's MIT license alongside the third-party notices. PowerShell build-script syntax validation passed.
- Both --demo --smoke-test and --smoke-test started and exited with code 0. Verified the embedded engine, capture script, banner and licenses, and checked ZIP integrity and the exact bundled EXE checksum.
- Release EXE: dist/Orbot-0.2.0.exe, 22,676,613 bytes. SHA-256: 70cfd83fc80b16499d3a2732d95b6c8cce4f1e334f0b2d23f4ccf75e4de31677.
- Portable ZIP: dist/Orbot-0.2.0-windows-x64.zip, containing the EXE, its checksum, instructions and licenses. SHA-256: bb385d42c6bc4d282ee82d8436ac3834bce5eddcfd94cd13cf1f723962b7f8b7.
- dist/SHA256SUMS.txt records both release hashes. No live Discord Quest was run or claimed during release verification.

Project cleanup verification, 26 October 2026:

- Moved development scripts into scripts/, documentation and design records into docs/, third-party notices into licenses/. Removed old binaries, generated spec files, completed plans and caches.
- Updated build, verification, launcher, screenshot output and documentation paths. All 18 local Markdown links resolved.
- Ran scripts/verify.ps1 from docs/ to verify working-directory independence: 29 engine tests, 7 loopback fixture tests, GUI smoke, Ruff, Mypy and medium/high Bandit checks passed.
- Ran scripts/build.ps1 without an output name from docs/: version read from the app, spec under build/spec/, work/cache under build/, current EXE under dist/.
- Rebuilt EXE passed both demo and normal startup/exit smoke checks; SHA-256 matched. No live Discord Quest was run.
- Retained the development environment, current executable, original assets, all three UI concepts, current screenshots and historical verification records. Temporary build/cache files were removed again after verification.

- Replaced the desktop presentation with the user-selected concept 3: slate/amber palette, horizontal navigation, queue left, focused task right, local decorative banner, slim progress and three-step task state.
- Preserved the existing controller and engine. No live Discord Quest was run or claimed during this UI update.
- Node engine suite: 29 passed.
- Python HTTP/WebSocket fixture suite: 7 passed. The initial sandbox run blocked loopback sockets (WinError 10013); the permitted local-fixture rerun passed.
- GUI smoke passed on real Tk widgets: add/deduplicate/reorder/remove/clear; queue preserved through filters and polls; full pending queue submitted to a mock worker; demo execution guard; Ctrl/Shift pointer selection; active task stays focused; Stop remains available on catalog/log views; 100% client progress does not imply confirmed completion; log navigation and error summary; connection dialog; minimum-size action visibility.
- Visual inspection: actual screenshots at 1360×900 and 1040×740, plus catalog and connection settings. The decorative banner is hidden at short heights so the action footer fits.
- Ruff passed; Mypy passed for all 9 application modules. Bandit: no medium/high findings (2 existing low-severity findings). Dependency check: no broken requirements.
- One-file Windows build passed: PyInstaller 6.22.3, Python 3.14.0, Pillow 13.0.0, bundled panorama and library licenses.
- Packaged EXE: both --demo --smoke-test and normal --smoke-test launched and exited with status 0.
- Artifact: dist/Orbot-0.2.0.exe, 22,678,130 bytes.
- SHA-256: 710155D8FEBD9D46D98909CAB21C2B616ECFA0C0BA8F57F51C5622F3CB9CF143
- Start-Orbot.cmd opens version 0.2.0, with a source fallback for development.

Actual UI: docs/images/focus-flow.png, docs/images/focus-flow-small.png, docs/images/catalog.png, docs/images/connection-settings.png.
Generated decorative asset and prompt provenance: orbot/assets/README.md.

The screenshots use clearly labeled offline sample data. Live activity/reward acceptance remains outside this UI validation.

---

# Verification — Orbot 0.1.3, 20 October 2026

## Executed checks

- Node engine tests: **29 passed**. Includes three-video sequential completion/claiming; game cleanup before the next video; continuing after an individual Quest or normal claim error; retaining entries on a fatal claim error; the in-flight claiming state; stopping/resuming without duplicate rewards; and running with auto-claim disabled then claiming completed Quests without replaying them. All prior module/API/cancellation cases remain covered.
- Python HTTP/WebSocket integration: **7 passed** against a real loopback fixture server. Includes Page/preload ordering and continuing to wait through a brief socket timeout rather than aborting a pending CDP operation.
- GUI smoke: passed using real Tk widgets and explicitly labeled sample data. Checked both tabs; add/deduplicate/reorder/remove/clear; keeping the queue through filtering and idle polling; passing all queue IDs to a fake worker despite selecting a single visible row; progress snapshots; disabled editing while running; clearing after completion; and layout at 1100×800 and 940×700. Demo Run is disabled and direct calls cannot submit work. The worker submission test temporarily disables the demo guard with a mock worker and makes no network calls. Application-window-only preview: `docs/design/legacy-ui.png`.
- Ruff: passed. Mypy: passed for all 7 application modules. Bandit: no medium or high findings; two low-severity findings remain.
- Runtime dependency check: no broken requirements.
- Windows one-file build: passed with PyInstaller 6.22.3 and Python 3.14.0.
- Packaged EXE: both `--demo --smoke-test` and normal `--smoke-test` launched and exited with status 0.

Run `scripts/verify.ps1` to repeat the source checks. The loopback fixture requires local socket access. Older release binaries were removed after version 0.2.0 was verified.

## Queue regression

The previous UI used only the Treeview selection as the run list. Filtering removed hidden rows from that selection, and there was no separate queue to inspect. The existing engine already contained a loop, so inspecting that loop alone could not explain every report of early termination. Its generic end message also concealed whether the loop exhausted its entries or encountered a fatal API error.

The revised UI has an independent ordered queue, submits all pending IDs, and keeps it across table selection/filter changes and snapshot polling. The engine owns a copy of the run IDs and exposes its queue status and reason for stopping. Nonfatal Quest/claim errors continue the loop; fatal authentication, HTML, captcha or access errors remain blocking and preserve pending entries. Full-queue submission and sequential execution are verified separately with real widgets and engine fixtures; no live reward was claimed during this change.

## Live connection regression

The reported connection failure was reproduced on Discord Desktop 1.0.9263. Property-presence probes matched lazy namespace objects instead of actual stores. The revised resolver inspects declared methods and prefers named store classes. Page-domain enablement and reloading the existing renderer were also added to the preload path.

The revised controller connected to the user's existing local Discord session and read 76 Orbs Quest records without starting or claiming any Quest. A second check after a fresh reload found QuestStore, UserStore, API, RunningGameStore and the dispatcher, with 2,646 module exports captured. This verifies the reported discovery failure on this build, not reward completion.

## Live HTML/API regression

The reported HTML response showed `/[object Object]`. Inspection of the selected client in the running Discord renderer identified a raw HTTP helper whose GET/POST signatures take a URL string, rather than Discord's authenticated REST client. Merely finding HTTP verb methods was insufficient.

The 0.1.2 resolver excludes raw HTTP helper objects, then verifies candidate clients using a non-mutating GET request. Verification checks a JSON user ID against the existing UserStore entirely inside Discord; no profile response is returned to the desktop app. The verified parameter convention is reused for all Quest calls.

The live connection test returned `ready=true`, `apiVerified=true`, `apiStyle=object`, and 76 Quest records. No Quest was enrolled, progressed or claimed. Regression fixtures verify that HTML responses stop the queue once and are never dumped into the log.

## Limits

The existing signed-in session was used only for connection/discovery checks. No login credentials were collected, no real Quest was run or claimed, and no Discord process was terminated. Live Quest completion remains unverified.

Mock results validate control flow and error handling; they do not prove that Discord will accept activity or award Orbs. The adapter can require changes when Discord updates its internal modules or request formats.



