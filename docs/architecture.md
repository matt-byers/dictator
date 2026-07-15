# Architecture

Dictator is a menu-less LaunchAgent app with one event-driven workflow:

```text
global hotkey → session coordinator → on-demand microphone
                                      ↓ release
                     local MLX transcription → clipboard paste
```

`SessionCoordinator` is the synchronization boundary. Its transitions are `idle → opening → recording → transcribing → pasting → idle`; failures briefly enter `error`. Every worker carries a monotonically increasing session ID, so work from an older session cannot modify a newer one.

`DictationController` owns the use case and depends only on four protocols: recorder, transcriber, inserter, and view. Native details live in focused adapters. The composition root in `main.py` is the only place they are assembled.

The app deliberately does not preload the model or retain a CoreAudio stream. This trades a small first-use latency for near-zero idle computation and no idle microphone indicator. MLX retains model weights after first use for fast later dictations, while its disposable buffer cache is capped and cleared after inference.

Native calls that have historically hung are guarded. CoreAudio close gets two seconds. Inference gets at least 45 seconds and scales to twice the audio duration plus 30 seconds, allowing long recordings on memory-pressured Macs. A timeout terminates the process and launchd restarts it. This bounds leaked native state more reliably than abandoning an unbounded series of Python threads.
