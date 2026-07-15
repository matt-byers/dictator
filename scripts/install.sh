#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
APP_SOURCE="$($ROOT/scripts/build-app.sh)"
APP_TARGET="$HOME/Applications/Whisper Dictate.app"
PLIST="$HOME/Library/LaunchAgents/com.local.whisper-dictate.plist"
UID_VALUE="$(id -u)"

launchctl bootout "gui/$UID_VALUE/com.local.whisper-dictate" 2>/dev/null || true
rm -rf "$APP_TARGET"
mkdir -p "$HOME/Applications" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/Whisper Dictate"
cp -cR "$APP_SOURCE" "$APP_TARGET"

sed "s|__APP_PATH__|$APP_TARGET|g" "$ROOT/packaging/com.local.whisper-dictate.plist.in" > "$PLIST"
launchctl bootstrap "gui/$UID_VALUE" "$PLIST"
launchctl kickstart -k "gui/$UID_VALUE/com.local.whisper-dictate"
echo "Installed and started: $APP_TARGET"
