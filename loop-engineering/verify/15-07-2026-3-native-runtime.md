# Checkpoint 3: bounded native runtime

## Scope

- Added lazy, on-demand CoreAudio capture with a hard 60-second sample bound.
- Added deterministic microphone teardown; a hung driver triggers a clean launchd restart instead of leaking threads.
- Added lazy local MLX transcription, deterministic decoding, a 128 MB cache cap, memory telemetry, and an inference watchdog.
- Added transcript-private rotating diagnostics and typed user-facing failures.
- Added a resilient global hotkey, thread-safe HUD, clipboard insertion, and the application composition root.

## Automated verification

- `python -m unittest discover -s tests -v`: 24 tests passed.
- `python -m compileall -q src tests`: passed.
- `git diff --check`: passed.

## Manual verification

Deferred until the standalone application bundle is built and installed.
