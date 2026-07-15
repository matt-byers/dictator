# Open-Source Hardening

## Linear Ticket
- **Ticket ID:** None
- **URL:** N/A

## Purpose & Impact

Turn Dictator from a machine-specific personal script into a small,
readable, well-tested open-source macOS application. Preserve its narrow
push-to-talk workflow while making privacy, lifecycle, performance, packaging,
and failure recovery explicit and reproducible.

Success means a contributor can clone the repository, run the hermetic tests,
build and install the app without editing absolute paths, follow live redacted
logs, and understand the architecture without reading one monolithic module.

## Requirements

### Functional Requirements

- [ ] FR1: `Control + Option + Space` starts exactly one dictation session when idle.
- [ ] FR2: The microphone opens only on demand and is released after recording.
- [ ] FR3: Releasing Space records bounded audio, transcribes locally, and inserts the result into the focused field.
- [ ] FR4: Sessions follow one legal state machine: idle → opening → recording → transcribing → pasting → idle/error.
- [ ] FR5: A new hotkey is rejected while any session is active.
- [ ] FR6: The event tap self-recovers when macOS disables it.
- [ ] FR7: User-facing failures identify microphone, permissions, model, timeout, and paste problems without exposing dictated text.
- [ ] FR8: Live logs rotate, remain tail-able, include session/timing/resource metadata, and redact transcripts by default.
- [ ] FR9: Build, install, restart, status, logs, doctor, and uninstall workflows are scripted.
- [ ] FR10: The app bundle has an editable vector icon source and generated macOS ICNS asset.

### Non-Functional Requirements

- [ ] NFR1: Idle microphone use is zero; steady idle CPU remains below 1% during a sampled verification run.
- [ ] NFR2: Recordings have a configurable duration/byte ceiling.
- [ ] NFR3: MLX decoding is deterministic, cache-bounded, timed, and resource growth is logged.
- [ ] NFR4: Fast tests import no MLX, PortAudio, Quartz, Tk, or user log files.
- [ ] NFR5: Core behavior has unit/component coverage for happy, failure, timeout, and concurrency paths.
- [ ] NFR6: A repeated-session soak verifies bounded threads, descriptors, and memory with fakes; an opt-in macOS live check verifies the real adapters.
- [ ] NFR7: The source repository contains no venv, model weights, logs, caches, generated signatures, private paths, or dictated text.
- [ ] NFR8: Code is typed, formatted, linted, and organized into focused modules without speculative abstraction.

### Out of Scope

- Publishing a GitHub repository or creating an external remote.
- Apple Developer ID signing, notarization, or binary release automation.
- App Store distribution.
- A settings window, menu-bar UI, configurable hotkey UI, or automatic updater.
- Supporting Intel Macs, Windows, or Linux.
- Guaranteeing termination of a native call inside the main process; timeouts that require hard isolation may use a supervised helper process.

### Assumptions (To Verify During Implementation)

- **MIT is the intended license:** Use the standard MIT text with Matthew Byers as copyright holder.
- **Source-built distribution is acceptable initially:** Verify a clean local build from a recreated environment; document that release notarization is deferred.
- **Bundle identity may stay configurable:** Default local builds to `com.local.dictator` to preserve existing permissions, with a build-time override for public releases.
- **“Live vlogging” means live operational logging:** Provide redacted rotating logs plus `scripts/manage.sh logs`.
- **A native launcher remains necessary for stable TCC identity:** Keep a small relative-path C launcher and verify the built bundle does not contain the developer’s home path.

## Technical Approach

Use a small `src` package with dependency-injected adapters. `SessionCoordinator`
owns the only mutable lifecycle state and exposes synchronous transition methods;
workers perform blocking audio/model/paste operations and report typed outcomes
back to it. Production adapters import native dependencies lazily, while tests use
fakes and import only pure Python modules.

```text
AppController
  ├── SessionCoordinator  (sole state machine and concurrency gate)
  ├── HotkeyService       (Quartz/pynput event tap)
  ├── AudioRecorder       (bounded on-demand CoreAudio capture)
  ├── Transcriber         (lazy MLX model, deterministic decode, timeout boundary)
  ├── TextInserter        (pasteboard + key injection)
  └── HUD / Diagnostics   (visible state + redacted rotating live logs)
```

Keep the public API intentionally small. Prefer dataclasses, enums, protocols,
and standard-library logging/concurrency. Generated artifacts are produced by
checked-in scripts: the icon pipeline renders `assets/icon.svg` with macOS
Quick Look, resizes with `sips`, and packages with `iconutil`; the app build
compiles `packaging/launcher.c` with `xcrun clang`/`python3-config`, stages the
package and environment under `Contents/Resources`, writes `Info.plist`, and
signs locally when a signing identity is supplied.

## Implementation Units

### Unit 1: Repository and reproducible project foundation
- **Changes:** `.gitignore`, `LICENSE`, `pyproject.toml`, `src/dictator/__init__.py`, `src/dictator/config.py`, `tests/unit/test_config.py`, `.github/workflows/test.yml`
- **Depends on:** none
- **Apply skills:** `python-testing-patterns`, `error-handling-patterns`
- **Self-Verification:** Create a fresh virtual environment; install the project with dev dependencies; run configuration tests; verify `git check-ignore` excludes `.venv`, bundles, caches, logs, and model artifacts; scan tracked candidates for `/Users/`.
- **Smoke Tests:**
  1. **Fresh contributor setup** — create a clean venv and install editable package → Expected: install completes without using the existing `.venv`.
  2. **Safe repository contents** — inspect Git status → Expected: local/runtime/generated artifacts are ignored.
- **Confidence Ceiling:** 95%

### Unit 2: Pure session state machine and app orchestration
- **Changes:** `src/dictator/state.py`, `src/dictator/app.py`, `tests/unit/test_state.py`, `tests/unit/test_app.py`
- **Depends on:** Unit 1
- **Apply skills:** `python-testing-patterns`, `error-handling-patterns`, `tdd-refactor-guard`
- **Self-Verification:** Run unit tests with native modules unavailable; verify every legal transition, invalid transition, hotkey-during-transcription rejection, release-during-open cancellation, failure recovery, and bounded recording deadline.
- **Smoke Tests:**
  1. **Normal session** — trigger, record, release, transcribe, paste → Expected: ordered states end at idle exactly once.
  2. **Overlapping hotkey** — trigger during transcription → Expected: no second stream or worker starts.
  3. **Failure recovery** — make each adapter fail → Expected: typed error is surfaced and the next session can start.
- **Confidence Ceiling:** 95%

### Unit 3: Native adapters, privacy-safe diagnostics, and performance guards
- **Changes:** `src/dictator/audio.py`, `src/dictator/transcriber.py`, `src/dictator/pasteboard.py`, `src/dictator/hotkey.py`, `src/dictator/diagnostics.py`, `tests/unit/test_audio.py`, `tests/unit/test_transcriber.py`, `tests/unit/test_pasteboard.py`, `tests/unit/test_hotkey.py`, `tests/unit/test_diagnostics.py`, `tests/integration/test_macos_adapters.py`, `tests/performance/test_session_soak.py`
- **Depends on:** Units 1 and 2
- **Apply skills:** `python-testing-patterns`, `error-handling-patterns`, `performance-profiling`
- **Self-Verification:** Run unit/component tests; run a fake 1,000-session soak and assert bounded thread/file-descriptor counts and stable application state; verify logs redact transcript content and rotate; verify partial stream-open failures close resources; verify recording and inference timeouts recover.
- **Smoke Tests:**
  1. **Idle privacy** — leave app idle → Expected: no audio stream exists and no transcript/model work occurs.
  2. **Redacted live logs** — dictate a known secret phrase → Expected: timings and character count appear, phrase does not.
  3. **Resource bounds** — repeat sessions → Expected: no monotonic thread, descriptor, frame-buffer, or MLX-cache growth beyond documented thresholds.
- **Confidence Ceiling:** 90%

### Unit 4: HUD, production entry point, and compatibility migration
- **Changes:** `src/dictator/hud.py`, `src/dictator/main.py`, `tests/unit/test_hud.py`, `tests/integration/test_entrypoint.py`, `dictate.py`, `run.sh`
- **Depends on:** Units 2 and 3
- **Apply skills:** `python-testing-patterns`, `error-handling-patterns`, `performance-profiling`
- **Self-Verification:** Verify the compatibility entry point delegates without import-time log/native side effects; test HUD rendering for opening, recording, transcribing, pasting, and actionable error states; sample idle CPU below 1% and confirm no microphone-open log before a hotkey.
- **Smoke Tests:**
  1. **Visible lifecycle** — complete a dictation → Expected: concise HUD states appear in order and hide at idle.
  2. **Actionable error** — deny/open-fail microphone → Expected: HUD explains the recovery action, then returns to usable idle.
- **Confidence Ceiling:** 85%

### Unit 5: Reproducible macOS bundle, installation, and icon pipeline
- **Changes:** `assets/icon.svg`, `packaging/launcher.c`, `packaging/Info.plist`, `packaging/launch-agent.plist.in`, `scripts/generate-icon.sh`, `scripts/build-app.sh`, `scripts/install.sh`, `scripts/manage.sh`, `scripts/uninstall.sh`, `tests/integration/test_packaging.py`
- **Depends on:** Units 1 and 4
- **Apply skills:** `error-handling-patterns`, `performance-profiling`
- **Self-Verification:** Generate ICNS from SVG; build app from a non-home temporary checkout; validate plist/signature; assert no `/Users/matthewbyers` bytes in source, launcher, plist, or bundle; install/bootstrap/status/log/bootout/uninstall against a temporary test label where possible.
- **Smoke Tests:**
  1. **Clean build** — build from a relocated checkout → Expected: valid app bundle with icon and no original absolute path.
  2. **Lifecycle scripts** — install, inspect status/logs, restart, uninstall → Expected: each operation is idempotent and clearly reported.
  3. **App identity** — inspect Finder/System Settings → Expected: Dictator name and icon are consistently displayed.
- **Confidence Ceiling:** 85%

### Unit 6: Open-source documentation and final live verification
- **Changes:** `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/architecture.md`, `docs/privacy.md`, `loop-engineering/verify/open-source-hardening.md`
- **Depends on:** Units 1 through 5
- **Apply skills:** `python-testing-patterns`, `performance-profiling`
- **Self-Verification:** Run the complete automated suite, clean install/build smoke, link/path checks, and documentation command checks; record exact live log excerpts and before/after CPU/memory/thread metrics in the verification artifact.
- **Smoke Tests:**
  1. **README journey** — follow setup through first dictation on a clean environment → Expected: no undocumented manual path edits.
  2. **Privacy journey** — inspect microphone indicator, logs, clipboard behavior, caches, and cleanup instructions → Expected: behavior matches documentation.
  3. **Live regression journey** — run five short dictations plus cancel/error cases → Expected: correct paste, mic release, stable event tap, bounded latency/resources.
- **Confidence Ceiling:** 80%

## Unit Execution Waves

```text
Wave 1: Unit 1
Wave 2: Unit 2
Wave 3: Unit 3
Wave 4: Unit 4
Wave 5: Unit 5
Wave 6: Unit 6
```

The work is intentionally sequential because each unit establishes contracts
used by the next, and final documentation must describe verified behavior rather
than planned behavior.

## Verification Plan

### Smoke Test Scenarios

1. **Idle resource/privacy check**
   - Launch the installed app and do not invoke it for at least 30 seconds.
   - Expected: microphone indicator remains off, idle CPU samples below 1%, and logs contain no audio/model activity.

2. **Cold and warm dictation**
   - Dictate a short phrase after launch, then a second phrase.
   - Expected: both paste correctly; cold/warm timings and MLX memory appear in redacted logs; microphone releases after each.

3. **Concurrency rejection**
   - Invoke the hotkey while transcription is active.
   - Expected: the active session remains coherent and no second recorder opens.

4. **Cancellation and permission failure**
   - Release before microphone open completes; separately exercise a mocked permission/open failure.
   - Expected: no stuck HUD/stream and the next session succeeds.

5. **Event-tap recovery**
   - Disable/mock the tap and invoke health polling.
   - Expected: tap is re-enabled and later hotkeys work.

6. **Repeated-session resources**
   - Run automated fake soak plus five real sessions.
   - Expected: bounded threads/descriptors/memory, rotating logs, and no transcript plaintext.

7. **Relocated clean build/install**
   - Build from a temporary checkout path and install through scripts.
   - Expected: valid signed/local app with icon, working launch agent, and no developer-specific paths.

### Agent Self-Verification

- `python -m unittest` or the final configured test runner exits 0.
- Coverage meets the configured threshold for pure core modules.
- Lint, formatting, typing, plist validation, code-sign verification, and absolute-path scans pass.
- Fresh-environment installation and relocated app build pass.
- Automated soak passes its resource thresholds.
- Live verification artifact records actual state, timing, memory, thread, log-redaction, and microphone lifecycle evidence.

## Spec Changelog

- 15-07-2026: Initial spec from production, testing, and open-source readiness audits.
