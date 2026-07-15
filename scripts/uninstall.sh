#!/bin/zsh
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.local.dictator.plist"
launchctl bootout "gui/$(id -u)/com.local.dictator" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.local.whisper-dictate" 2>/dev/null || true
rm -f "$PLIST"
rm -f "$HOME/Library/LaunchAgents/com.local.whisper-dictate.plist"
rm -rf "$HOME/Applications/Dictator.app"
rm -rf "$HOME/Applications/Whisper Dictate.app"
echo "Dictator was removed. Models and logs were left intact."
