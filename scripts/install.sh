#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
APP_SOURCE="$($ROOT/scripts/build-app.sh)"
APP_TARGET="$HOME/Applications/Dictator.app"
PLIST="$HOME/Library/LaunchAgents/com.local.dictator.plist"
UID_VALUE="$(id -u)"

# Remove the pre-rename installation, if present.
launchctl bootout "gui/$UID_VALUE/com.local.whisper-dictate" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.local.whisper-dictate.plist"
rm -rf "$HOME/Applications/Whisper Dictate.app"

launchctl bootout "gui/$UID_VALUE/com.local.dictator" 2>/dev/null || true
rm -rf "$APP_TARGET"
mkdir -p "$HOME/Applications" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/Dictator"
cp -cR "$APP_SOURCE" "$APP_TARGET"

sed "s|__APP_PATH__|$APP_TARGET|g" "$ROOT/packaging/com.local.dictator.plist.in" > "$PLIST"
launchctl bootstrap "gui/$UID_VALUE" "$PLIST"
launchctl kickstart -k "gui/$UID_VALUE/com.local.dictator"
echo "Installed and started: $APP_TARGET"
