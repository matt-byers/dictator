# Contributing

Bug fixes should begin with a failing regression test. Keep platform APIs behind the existing ports, avoid module-level native initialization, and never log transcript content by default.

Before opening a change, run:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/coverage run -m unittest discover -s tests
.venv/bin/coverage report
.venv/bin/ruff check src tests
scripts/build-app.sh
codesign --verify --deep --strict "build/Whisper Dictate.app"
```

Manual changes to hotkeys, capture, inference, or paste behavior also require one real dictation and inspection of the resulting log.
