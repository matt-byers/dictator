#!/bin/zsh
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.local.whisper-dictate.plist"
launchctl bootout "gui/$(id -u)/com.local.whisper-dictate" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/Applications/Whisper Dictate.app"
echo "Whisper Dictate was removed. Models and logs were left intact."
