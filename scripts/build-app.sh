#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
PYTHON="$ROOT/.venv/bin/python"
APP="$ROOT/build/Whisper Dictate.app"
CONTENTS="$APP/Contents"
RESOURCES="$CONTENTS/Resources"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing .venv. Run scripts/bootstrap.sh first." >&2
  exit 1
fi

"$ROOT/scripts/generate-icon.sh" >/dev/null
rm -rf "$APP"
mkdir -p "$CONTENTS/MacOS" "$RESOURCES/python"
cp "$ROOT/packaging/Info.plist" "$CONTENTS/Info.plist"
cp "$ROOT/build/AppIcon.icns" "$RESOURCES/AppIcon.icns"
cp -R "$ROOT/src/whisper_dictate" "$RESOURCES/python/"

SITE_PACKAGES="$($PYTHON -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
cp -cR "$SITE_PACKAGES" "$RESOURCES/site-packages"

PYTHON_CONFIG="$($PYTHON -c 'import pathlib, sys; print(pathlib.Path(sys.base_prefix) / "bin/python3.13-config")')"
cc "$ROOT/packaging/launcher.c" -o "$CONTENTS/MacOS/WhisperDictate" \
  $($PYTHON_CONFIG --cflags) $($PYTHON_CONFIG --embed --ldflags)
codesign --force --deep --sign - "$APP"
echo "$APP"
