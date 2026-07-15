# Checkpoint 5: installed smoke verification

## Scope

- Installed the new bundle at `~/Applications/Dictator.app`.
- Replaced the legacy LaunchAgent and confirmed launchd keeps the new executable running.
- Caught and fixed a bundle-relative resource path defect exposed by the first launch.
- Prevented runtime bytecode writes from invalidating the signed bundle seal.

## Automated and live verification

- LaunchAgent state remained `running` without additional restart attempts after the fix.
- Startup log recorded `app_started` with the Q4 model and no runtime traceback.
- Five idle samples measured 0.1–0.7% CPU.
- Idle physical footprint measured 46.3 MB (48.3 MB peak).
- No PortAudio, MLX model, or Hugging Face model files were loaded while idle.
- A synthetic macOS speech sample transcribed correctly as `Howdy.`.
- Cold-process end-to-end transcription completed in 9.47 seconds; the one-time model load was included.
- Synthetic transcription used no swap and a maximum resident set of 479 MB; MLX peak footprint was 1.45 GB.
- Generated ICNS was visually inspected at 1024×1024 and retained clean rounded geometry and waveform contrast.

## Manual verification

Input Monitoring and Accessibility must be granted to the newly installed bundle before the global-hotkey test. A real microphone dictation remains the final human gate.
