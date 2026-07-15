# Security and privacy

Audio and transcription run locally. Captured samples live only in memory for the current session. Logs contain timings, sizes, states, and memory metrics but omit transcript content unless the user explicitly enables `DICTATE_LOG_TRANSCRIPTS=1`.

Dictator needs macOS Microphone, Input Monitoring, and Accessibility permissions to perform its core function. It does not need network access after the model has been downloaded, although the first model use contacts Hugging Face.

Report a security or privacy issue privately to the repository owner before opening a public issue. Include the version, macOS version, reproduction steps, and relevant redacted logs. Do not include dictated text or audio.
