# Checkpoint 6: Dictator release identity

## Scope

- Renamed the repository-facing project, Python package, executable, app bundle, bundle ID, LaunchAgent, logs, documentation, and test imports to Dictator.
- Set the public description to “A free speech-to-text app using Whisper.”
- Added automatic removal of the pre-rename installation.

## Verification

- `ruff check src tests`: passed.
- `python -m unittest discover -s tests -v`: 21 tests passed.
- `coverage report`: 89% covered (80% gate).
- `python -m compileall -q src tests`: passed.
- Installed LaunchAgent `com.local.dictator` remained running at 0.2% idle CPU and 36 MB RSS.
- Installed `Dictator.app` passed post-launch strict code-signature verification.
- Installed app and LaunchAgent plists passed `plutil -lint`.
- The old app bundle and LaunchAgent were removed.

## Human gate

Grant Input Monitoring, Accessibility, and Microphone permissions to `~/Applications/Dictator.app`, then perform one real hotkey dictation.
