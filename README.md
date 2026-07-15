# Dictator

A free speech-to-text app using Whisper.

Hold **Control + Option + Space**, wait for the listening indicator, speak, and release Space. Dictator transcribes locally with MLX Whisper and pastes into the focused app. It sends no audio or text to a server and requires no API key.

## Design principles

- **Quiet when idle:** no microphone stream, model load, or inference work until the hotkey is pressed.
- **Private by default:** audio stays in memory and transcript content is excluded from logs.
- **Bounded resources:** recordings stop at five minutes, MLX's free cache is capped at 128 MB, logs rotate, and stuck native work causes a clean launchd restart rather than leaked threads.
- **One session at a time:** a small state machine rejects overlapping hotkeys and stale workers.
- **Observable:** lifecycle, latency, audio metadata, and MLX memory are written to a local rotating log.

## Requirements

- Apple Silicon Mac running macOS 13 or later
- Python 3.13 from [python.org](https://www.python.org/downloads/macos/)
- Xcode Command Line Tools (`xcode-select --install`)
- About 2 GB for Python dependencies and the one-time model download

## Install from source

```sh
git clone https://github.com/matt-byers/dictator.git
cd dictator
scripts/bootstrap.sh
scripts/install.sh
```

The installer builds and ad-hoc signs `Dictator.app`, installs it in `~/Applications`, and registers a per-user LaunchAgent. The bundle uses APFS clone copies where supported to avoid needless extra physical disk use during local builds.

Grant **Dictator** these one-time permissions in System Settings → Privacy & Security:

1. Microphone — recording while the hotkey is held.
2. Input Monitoring — receiving the global hotkey.
3. Accessibility — sending Command+V.

For Input Monitoring and Accessibility, use the `+` button and select
`~/Applications/Dictator.app`. Microphone permission is requested on the first recording.

Restart after changing permissions:

```sh
launchctl kickstart -k gui/$(id -u)/com.local.dictator
```

## Usage and diagnostics

The HUD progresses through Opening microphone → Listening → Transcribing → Pasting, then disappears. The microphone is closed before transcription begins.

```sh
# Follow privacy-safe application events
tail -f "$HOME/Library/Logs/Dictator/app.log"

# Inspect launch/runtime errors
tail -f /tmp/dictator.stderr.log

# Restart
launchctl kickstart -k gui/$(id -u)/com.local.dictator

# Remove the app and LaunchAgent (models and logs remain)
scripts/uninstall.sh
```

Logs include character and word counts, never transcript text, unless `DICTATE_LOG_TRANSCRIPTS=1` is explicitly set.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DICTATE_MODEL` | `mlx-community/whisper-large-v3-turbo-q4` | Quantized local model |
| `DICTATE_LANG` | `en` | Language code; empty enables detection |
| `DICTATE_MAX_SECONDS` | `300` | Hard recording duration and memory bound |
| `DICTATE_MLX_CACHE_MB` | `128` | MLX reusable-buffer cache cap |
| `DICTATE_DEBUG` | `0` | More diagnostic events |
| `DICTATE_LOG_TRANSCRIPTS` | `0` | Opt in to plaintext transcript logs |

Add overrides to the LaunchAgent's `EnvironmentVariables` dictionary, then restart it.

## Development

```sh
scripts/bootstrap.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/coverage run -m unittest discover -s tests
.venv/bin/coverage report
.venv/bin/ruff check src tests
scripts/build-app.sh
```

The package is intentionally split into a pure session coordinator, an orchestration controller, and narrow macOS adapters. Heavy native dependencies are imported lazily. See [Architecture](docs/architecture.md), [Contributing](CONTRIBUTING.md), and [Security](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
