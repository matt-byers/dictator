# Checkpoint 4: open-source application bundle

## Scope

- Added the original SVG application icon and generated multi-resolution ICNS asset.
- Replaced machine-specific launcher paths with a bundle-relative embedded-Python launcher.
- Added reproducible bootstrap, build, install, and uninstall scripts.
- Added a signed background-app bundle and launchd template.
- Rewrote the README and added architecture, contribution, security, and license documentation.
- Removed the legacy monolith and migrated its critical regressions to focused package tests.

## Automated verification

- `python -m unittest discover -s tests -v`: 21 tests passed.
- `coverage report`: 89% covered (80% gate).
- `ruff check src tests`: passed.
- `python -m compileall -q src tests`: passed.
- `plutil -lint`: app and LaunchAgent property lists passed.
- `codesign --verify --deep --strict`: application bundle passed.
- Generated `AppIcon.icns` was recognized as a macOS icon file.

## Manual verification

Pending installation and a real push-to-talk dictation.
