# Voice Implementation Comparison

## 1. Executive conclusion

**Recommendation: Option D.** Use the separate `voice-tools` package, now housed in `/home/xzhang/dev/voice-assist`, as the canonical speech-input base, then harden it before wider adoption. Keep the extracted VoiceAssist prototype isolated in that repository and migrate only useful browser/WebSocket transport and voice-session policies into a future `bot0-voice-assistant` application. Do not use VoiceAssist as the speech-core base.

`voice-tools` is already an installable `src`-layout package with a small Python API, CLI, declared dependencies, temporary-file cleanup, domain-specific errors, and five hardware/network-independent tests. VoiceAssist is a coupled vehicle-manual assistant prototype: its active transcription path uses Google Speech Recognition, writes `debug_audio.wav`, loads local pickles and a sentence-transformer model, calls an LLM, and invokes TTS from one service class.

AgenticAICompass does **not** currently contain or import speech code. Its checked-in `pyproject.toml`, `requirements.txt`, and `uv.lock` do not declare `voice-tools`. Its local virtual environment previously had an editable installation pointing to `/home/xzhang/voice-tools`; the reusable project is now housed at `/home/xzhang/dev/voice-assist`, and a machine-local editable link is not reproducible application integration.

`voice-tools` is the better base, not yet a complete cross-platform canonical layer. Its only public operation is a blocking WSLg/PulseAudio-to-OpenAI flow. It still needs separate capture/transcription contracts, `transcribe_file`, explicit client/configuration injection, and platform adapters.

## 2. Repository and component inventory

### Extracted VoiceAssist prototype

| Area | Classification | Evidence and responsibility |
| --- | --- | --- |
| `VoiceAssist_sockets.py` | Application orchestration + transport + input/output | FastAPI app, `Transcriber`, WebSocket buffering, Google transcription, wake-word policy, retrieval, LLM call, and `pyttsx3` output are combined. |
| `VoiceAssist_sockets_GOLD.py` | Experiment/variant | Near-duplicate server with different buffer windows and overlap sizes. |
| `VoiceAssist_sockets_backup.py` | Backup/experiment | Adds unused `whisper` import/model path, native `AudioCapture`, rotating debug WAVs, and an older WebSocket flow. |
| `webfrontend.html`, `frontendold.html` | Transport/client | Browser microphone capture with `getUserMedia`, PCM conversion, and hard-coded `ws://127.0.0.1:8000/listen/`. |
| `websockettest.py` | Manual integration script | Converts a named WAV and streams it to a running local WebSocket server; executes immediately on import. |
| `playback.py` | Speech-output utility | Reads a WAV with `soundfile` and plays it through `sounddevice`; prints instead of returning metadata. |
| `llamav2.py`, `llamav2SAVED.py`, `globals.py` | Application LLM integration | Local llama.cpp/OpenAI chat, `config.ini`, global environment mutation, global clients, and credential printing. |
| `search_vectors.py`, `store_vectors.py`, `common_modules.py` | Retrieval/application data | PDF extraction, sentence-transformer embeddings, pickle persistence, and vector search for the Prius manual. |
| `socket_helper.py` | Experimental transport | Print-oriented raw TCP helper; not used by the active server. |
| WAV/PDF/PKL files and `llamav2.zip` | Fixtures, generated data, and artifacts | About 14 MB of recordings, debug output, document data, embeddings, and a source backup archive. |
| `requirements.txt`, `Dockerfile` | Broken deployment metadata | Flat application dependency dump; Dockerfile references absent `requirements2.txt`. No package metadata exists. |

There is no `VoiceAssist/__init__.py`, `pyproject.toml`, setup configuration, package namespace, or automated test directory.

### AgenticAICompass and voice-tools

| Area | Classification | Evidence and responsibility |
| --- | --- | --- |
| AgenticAICompass checked-in source | Application with no speech integration | No `voice_tools`/`voice-tools` imports, dependency, transcription route, microphone client, or speech test was found. `frontend/next.config.ts` and `api/main.py` explicitly set microphone permissions to disabled. |
| AgenticAICompass `.venv` | Local-machine integration only | The historical `__editable__.voice_tools-0.1.0.pth` pointed to `/home/xzhang/voice-tools`; `.venv/bin/voice-to-text` exposed the package CLI. |
| `/home/xzhang/dev/voice-assist/pyproject.toml` | Reusable package metadata | Defines project `voice-tools`, Python `>=3.10`, `src` discovery, dependencies, pytest group, and `voice-to-text` entry point. |
| `src/voice_tools/speech.py` | Reusable but coupled speech input | Records through `parecord`, verifies a temporary WAV, calls OpenAI `whisper-1`, translates provider errors, returns text, and removes the WAV. |
| `src/voice_tools/cli.py` | CLI adapter | Calls `transcribe_from_microphone`, writes status/errors to stderr and transcript to stdout. |
| `src/voice_tools/__init__.py` | Public Python API | Exports only `transcribe_from_microphone`. |
| `tests/test_speech.py` | Offline unit tests | Fakes `parecord`, WAV generation, terminal input, OpenAI, environment loading, and CLI output. |

The files named `*_product_voice.py` in AgenticAICompass concern writing style, not audio or speech.

## 3. Runtime-flow comparison

### VoiceAssist active browser flow

```text
browser getUserMedia
→ Web Audio float samples
→ 16-bit PCM chunks
→ WebSocket /listen/
→ FastAPI byte buffer
→ overwrite debug_audio.wav
→ SpeechRecognition.recognize_google
→ wake-word/done-word accumulation
→ sentence-transformer + docs_and_embeddings.pkl retrieval
→ OpenAI chat or local llama.cpp
→ pyttsx3 playback
→ transcription/response JSON over WebSocket
```

`Transcriber.__init__` constructs `speech_recognition.Recognizer` and `vector_search`, then immediately loads a named sentence-transformer and two working-directory pickle files. Transcription therefore cannot be instantiated independently of retrieval data. `process_command` requires the LLM and retrieval result; `voice_response` constructs TTS directly.

The backup variant has a native PyAudio capture loop, but the active server receives browser audio. The backup imports `whisper` and declares `WHISPER_MODEL_PATH = "ggml_base.en.bin"` without loading or using either; its actual transcription is still `recognize_google`.

### voice-tools flow

```text
Python call or voice-to-text CLI
→ load package-root .env
→ require OPENAI_API_KEY and parecord
→ parecord mono 16 kHz WAV in TemporaryDirectory
→ soundfile verification
→ OpenAI audio.transcriptions.create(model="whisper-1")
→ stripped transcript string
→ temporary WAV cleanup
```

This path is independent of WebSockets, frontend, retrieval, LLM chat, TTS, Docker, and the caller's current working directory. It is not independent of OpenAI, PulseAudio's `parecord`, environment configuration, or terminal input: `transcribe_from_microphone()` blocks on `input()` and constructs `OpenAI()` internally.

### AgenticAICompass consumption

There is no checked-in runtime flow. The local editable install makes `voice-to-text` and `import voice_tools` available only in the existing developer virtual environment. No AgenticAICompass source consumes them.

## 4. Capability comparison

“AgenticAICompass / voice-tools” below evaluates the discovered `/home/xzhang/dev/voice-assist` package and notes where AgenticAICompass integration is absent.

| Capability | VoiceAssist | AgenticAICompass / voice-tools |
| --- | --- | --- |
| Installable package | **No** — no package metadata or namespace. | **Yes** — `pyproject.toml`, `src/voice_tools`, setuptools discovery. AgenticAICompass does not declare it. |
| Python API | **Partial** — `Transcriber` exists but requires LLM/retrieval construction and returns mostly `None` until wake-word completion. | **Yes** — `transcribe_from_microphone() -> str`; narrow and blocking. |
| CLI | **No** — runnable server/manual scripts only. | **Yes** — `voice-to-text = voice_tools.cli:main`. |
| Microphone capture | **Partial** — browser capture is active; native PyAudio exists only in backup code. | **Yes** — `parecord` capture, limited to PulseAudio/WSLg-like environments. |
| File transcription | **Partial** — `websockettest.py` can stream a WAV to a running server; no direct API. | **No** — `_transcribe_audio(Path)` is private and OpenAI-specific. |
| Device enumeration | **No**. | **No**. |
| Local Whisper | **No** — dependency/import/path exist, but no model is loaded or called. | **No** — OpenAI `whisper-1` is remote. |
| Remote transcription | **Yes** — Google through `recognize_google`. | **Yes** — OpenAI transcription API. |
| WebSocket transport | **Yes** — browser and Python client plus FastAPI endpoint. | **No**. |
| TTS/audio output | **Yes** — `pyttsx3` and `sounddevice` playback. | **No**. |
| Offline operation | **No** — active STT is remote and the assistant path calls remote/local services. | **No** — OpenAI transcription is mandatory. |
| Dependency injection | **Partial** — LLM is passed to `Transcriber`; recognizer, retrieval, model, files, and TTS are constructed internally. | **No** — OpenAI client, recorder command, environment path, model, and stop mechanism are fixed. |
| Automated tests | **No** — `websockettest.py` is a manual server/file script. | **Yes** — five offline unit tests mock hardware and OpenAI. |
| Windows support evidence | **Partial** — Windows packages are pinned and browser capture may work, but the Linux Dockerfile and untested native stack conflict. | **No** — unconditional `parecord` requirement; no Windows adapter or test. |
| WSL support evidence | **Unknown** — no WSL-specific code or documentation. | **Partial** — package description targets WSLg and uses PulseAudio `parecord`; no hardware test or setup guide. |
| Linux support evidence | **Partial** — Linux Docker native libraries are listed, but the Docker build references a missing file. | **Partial** — `parecord` is a Linux/PulseAudio path, with mocked tests only. |
| Application coupling | **Yes** — vehicle retrieval, wake word, LLM, FastAPI, and TTS are in the transcription service. | **No** in the package; **Yes** operationally for AgenticAICompass's undeclared editable local path. |
| Generated-data coupling | **Yes** — required pickle files and overwritten debug WAVs use the current directory. | **No** — a private temporary directory is cleaned in `finally`. |
| Portability risk | **Yes (high)** — packaging, dependency, cwd, network, and application coupling. | **Partial (medium)** — good package boundary, but fixed WSLg/Pulse/OpenAI/terminal assumptions. |

## 5. Portability analysis

### Packaging and installation

VoiceAssist cannot be installed independently. Its bare imports (`from llamav2 import ...`, `from search_vectors import ...`) require its directory on `sys.path` or a matching working directory. `requirements.txt` contains invalid `openai=1.54.4` syntax, mixes speech core with Torch, Whisper, transformers, FAISS, PDF, Windows, and TTS dependencies, and omits active imports such as FastAPI, Uvicorn, websockets, pydub, sounddevice, and gTTS. Its Dockerfile copies nonexistent `requirements2.txt`.

`voice-tools` has a valid build system and `src` layout. Core Python dependencies are only `openai`, `python-dotenv`, and `soundfile`; `pytest` is separated. The external `parecord` executable is a mandatory but undeclared system dependency. OpenAI is mandatory even for import because `speech.py` imports SDK symbols eagerly, though it does not create a client at import time.

AgenticAICompass does not declare the package in any manifest or lockfile. Its editable `.pth` absolute path is the largest immediate integration risk: a clean checkout cannot reproduce it.

### Platform assumptions

VoiceAssist's browser capture is the most platform-neutral capture concept, but it is tied to localhost WebSockets and the browser's Web Audio behavior. The server assumes mono 16-bit PCM at 16 kHz without a negotiated audio envelope. The backup PyAudio path assumes a default input device and provides no discovery or selection. `pyttsx3` selects `voices[1]`, which may not exist or represent the intended voice. No platform tests exist.

`voice-tools` invokes `parecord` by name with fixed mono/16 kHz/s16le/WAV arguments. This is evidence for PulseAudio-compatible Linux/WSLg, not native Windows or macOS support. It has no device listing or selection. No claim beyond mocked WSLg/Pulse-oriented behavior is currently justified.

### Configuration and filesystem behavior

VoiceAssist reads `config.ini` from the current directory, mutates `OPENAI_API_KEY`, prints the credential, hard-codes local service URLs and models, and reads/writes fixed relative filenames. Loading `SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")` can trigger an implicit model download. No tracked API key was found, but the credential-printing behavior is unsafe.

`voice-tools` does not read configuration at import time. Each public call loads `ENV_PATH`, computed from the source package location, and then reads `OPENAI_API_KEY`. That is predictable in the editable source checkout but is a poor installed-package contract: a wheel installation would look for `.env` relative to installed package files. An ignored `.env` exists in the local `voice-assist` checkout; its contents were not inspected. Audio is created only under `TemporaryDirectory` and explicitly removed.

### API design

VoiceAssist has no stable public API, type contracts, or structured speech result. Exceptions are generally logged and converted to `None`; transcription is inseparable from wake-word/session state. The active browser protocol is implicit raw PCM.

`voice-tools` provides a clear `str` return and detailed package errors. Its public function has no arguments, however, so callers cannot provide a recorder, OpenAI client, model, timeout, device, audio source, stop signal, or configuration. The library function also calls terminal `input()`, making it unsuitable for headless application orchestration despite being callable from Python. No async API exists.

## 6. Dependency and packaging analysis

### Speech-core dependency weight

- VoiceAssist active speech path: `SpeechRecognition`, NumPy, and a remote Google service.
- VoiceAssist transport/output: FastAPI, Starlette, Uvicorn, WebSockets, PyAudio/PortAudio, `pyttsx3`, sounddevice, soundfile, pydub/ffmpeg.
- VoiceAssist unrelated application stack: OpenAI chat, requests/llama.cpp, sentence-transformers, Torch, transformers, FAISS, PDF libraries, pickles, and vehicle assets.
- voice-tools core: OpenAI SDK, python-dotenv, soundfile, and external PulseAudio `parecord`.

The `openai-whisper`, Torch, and transformers pins in VoiceAssist are heavy but do not provide a working local Whisper path. `voice-tools` is materially lighter, though OpenAI should become an optional backend extra once a provider protocol exists.

### Separation

VoiceAssist does not separate capture, transport, STT, wake-word policy, retrieval, LLM completion, or TTS. `voice-tools` separates CLI from speech implementation and excludes application concerns, but capture and remote transcription remain fused in one public operation.

The intended dependency direction should be:

```text
AgenticAICompass ───────────────┐
                               ├──> voice-tools
bot0-voice-assistant ───────────┘
          │
          └── optional bot0-thought-graph

voice-tools ─X─> AgenticAICompass
voice-tools ─X─> bot0-voice-assistant
bot0-thought-graph ─X─> voice-tools
```

## 7. Testability analysis

VoiceAssist has no unit tests. `websockettest.py` requires named local WAV files, pydub/ffmpeg, a live localhost WebSocket server, remote transcription, retrieval artifacts, and configured LLM services. It writes a converted WAV and executes `asyncio.run()` at import. The active server configures logging at import and writes `debug_audio.wav` during every transcription attempt.

`voice-tools/tests/test_speech.py` is a useful base. It fakes the process, creates a deterministic WAV, replaces terminal input and OpenAI, verifies transcript return and cleanup, checks missing API key/`parecord` errors, and tests CLI streams/exit codes. Missing critical tests include:

- invalid/empty WAV and nonzero `parecord` exit;
- process timeout/kill behavior;
- each OpenAI exception translation and malformed response;
- import with no API key and no client construction;
- wheel/install behavior and use outside the repository;
- caller-supplied configuration/client;
- file transcription;
- platform adapter selection;
- cancellation without terminal input.

AgenticAICompass has no tests proving package installation, import, or application consumption.

## 8. Duplicate implementation analysis

| Overlap | Better implementation | Reason |
| --- | --- | --- |
| Microphone capture | **Depends on use**: voice-tools for Python/WSLg batch capture; VoiceAssist browser capture for web streaming | voice-tools cleans up and is tested; VoiceAssist uniquely captures in-browser but has no protocol abstraction or tests. |
| WAV creation | **voice-tools** | Temporary location, `soundfile` verification, deterministic mono/16 kHz request, and cleanup. VoiceAssist overwrites working-directory debug files. |
| Remote transcription | **voice-tools** | Direct API, returned text, typed errors, and mocked tests. VoiceAssist swallows Google errors into `None` and couples recognition to wake-word state. |
| OpenAI setup | **voice-tools** | Client is created at call time and provider errors are translated. VoiceAssist reads cwd config, mutates globals, and prints credentials. |
| Whisper setup | **voice-tools**, narrowly | It correctly calls remote `whisper-1`. VoiceAssist's local Whisper import/path are dead code. Neither has a local backend. |
| Temporary-file cleanup | **voice-tools** | `TemporaryDirectory` plus `finally`; VoiceAssist retains/rotates debug files. |
| Error handling | **voice-tools** | Named error hierarchy versus broad logging/printing and `None`. |
| Audio playback/TTS | **VoiceAssist only** | It has working-looking adapters, but they belong in an optional output package/application and lack tests/device injection. |
| Streaming framing | **VoiceAssist only** | Browser PCM-to-WebSocket flow is unique, but framing is implicit and should be extracted as transport—not STT core. |

## 9. Unique VoiceAssist capabilities

| Capability | Classification | Disposition |
| --- | --- | --- |
| Browser microphone capture and PCM WebSocket streaming | Reusable optional integration | Extract protocol and browser/server adapters into `bot0-voice-assistant`; define sample format and session framing explicitly. |
| WebSocket buffering, overlap, timeout, and disconnect handling | Reusable optional integration | Preserve as behavioral reference; rewrite behind tests because current variants disagree on buffer sizes. |
| Wake-word, done-word, and timed command accumulation | Voice-assistant application functionality | Extract as a replaceable session policy, not speech core. |
| Amplitude silence threshold | Experiment | Preserve as reference only; it is not a robust VAD and does not currently decide transcription boundaries consistently. |
| `pyttsx3` TTS and WAV playback | Reusable optional speech-output integration | Move only after adding engine/device injection and offline tests; keep outside STT core. |
| Native PyAudio capture | Experiment/obsolete duplicate | Do not migrate as-is; it exists only in backup code and lacks selection, errors, and tests. |
| Vehicle-manual retrieval and local llama.cpp/OpenAI response | Voice-assistant application functionality | Preserve only with the vehicle assistant prototype; never move into `voice-tools`. |
| Local Whisper declarations | Obsolete/incomplete | Do not extract; no implementation exists. |
| Debug WAVs, PDF, pickles, recordings, zip, GOLD/backup variants | Generated data and experiments | Classify fixtures individually, then archive; do not package. |

## 10. Recommended canonical architecture

Adopt `voice-tools` as the package identity and evolve it around these boundaries:

```text
voice_tools
├── capture
│   ├── AudioCapture protocol
│   ├── PulseAudio/parecord adapter
│   └── future native platform adapters
├── transcription
│   ├── Transcriber protocol
│   ├── OpenAI adapter (optional extra)
│   └── future local Whisper adapter (optional extra)
├── models
│   ├── AudioFormat
│   └── TranscriptResult
├── API
│   ├── list_audio_devices(...)
│   ├── record_audio(...)
│   ├── transcribe_file(...)
│   └── transcribe_from_microphone(...)
└── CLI
```

Core APIs should accept explicit dependencies/configuration and return typed results. Environment loading belongs in the CLI or an explicit loader, not the library operation. OpenAI, local Whisper, and platform capture stacks should be optional adapters. WebSockets, wake words, assistant sessions, retrieval, LLM response generation, TTS, and playback remain outside the speech-to-text core.

AgenticAICompass should declare a released version or pinned Git revision of `voice-tools` in package metadata and inject its chosen transcription/capture adapters from application startup. It should not rely on an editable absolute path. The current microphone-denying response policies must be revisited only if AgenticAICompass adds browser capture.

## 11. Recommended VoiceAssist disposition

Choose **extract reusable pieces first, then archive the remainder**.

The prototype has been extracted to `voice-assist/prototypes/legacy_voice_assist/`. Keep it isolated until the browser PCM protocol, buffering behavior, wake-word policy, TTS behavior, and useful audio fixtures are classified and covered by replacement tests. Future migration belongs in a separate `bot0-voice-assistant` application repository.

The future repository should be named `bot0-voice-assistant`. It should consume `voice-tools` and may optionally consume `bot0-thought-graph`; it should own WebSockets, UI, session orchestration, wake words, retrieval, LLM interactions, and TTS. It should not own a second Whisper implementation.

## 12. Phased migration plan

| Phase | Scope and repository | Expected result | Main risk | Validation |
| --- | --- | --- | --- | --- |
| 1. Establish canonical API | `/home/xzhang/dev/voice-assist`: separate capture from transcription; add typed audio/transcript models, `transcribe_file`, injected backend/client/config. | Headless, testable speech core with current OpenAI behavior preserved. | Breaking the existing no-argument API/CLI. | Compatibility test, wheel install/import, no import-time client/env access, offline unit tests. |
| 2. Add portability boundaries | `voice-tools`: make Pulse capture and OpenAI optional adapters; document WSLg; add platform capability errors and adapter contracts. | Honest platform support and lightweight custom/file-only installs. | Native audio behavior differs by OS and device. | CI without audio hardware, mocked adapter matrix, one manual smoke test per claimed platform. |
| 3. Integrate AgenticAICompass | AgenticAICompass: add a pinned dependency and an application service consuming the public API; remove reliance on `.venv` editable path. | Reproducible installation and one owned consumption path. | Blocking microphone API in async/web runtime. | Clean-environment install, fake-backend application test, no API/network in tests. |
| 4. Extract VoiceAssist integrations | New `bot0-voice-assistant`: extract browser/WebSocket protocol, session/wake-word policy, and optionally TTS/playback adapters. | Standalone assistant application consuming `voice-tools`. | Preserving undocumented PCM/buffer semantics and browser compatibility. | Recorded PCM fixtures, WebSocket contract tests, disconnect/cancellation tests, no retrieval/LLM dependency in transport tests. |
| 5. Archive prototype | `voice-assist` and `bot0-voice-assistant`: classify fixtures and migrate the documented legacy prototype incrementally. | Thought-graph repo has no voice application; no unique behavior is lost. | Deleting the only example of an edge behavior. | Traceability checklist from this report, replacement tests, file-by-file disposition review. |

## 13. Risks and unresolved questions

- Which operating systems must be supported first? Current evidence supports only a WSLg/Pulse-oriented `voice-tools` path, not Windows/macOS/native Linux broadly.
- Does AgenticAICompass need browser streaming, server-side microphone capture, file upload, or only a developer CLI? Its source currently implements none.
- What latency/streaming requirement exists? `voice-tools` is batch-only; VoiceAssist streams transport but transcribes multi-second buffers as batch calls.
- Which local STT backend, model size, hardware, and redistribution policy are acceptable? Neither implementation has functioning local Whisper.
- Should transcript results include timestamps, language, confidence, duration, provider/model, and raw metadata? Current APIs return only text.
- How should cancellation work in services? `input()` is acceptable for CLI use but not library/application use.
- Which VoiceAssist recordings are legitimate redistributable test fixtures? Their provenance and sensitivity were not established.
- The active VoiceAssist server assumes raw mono 16 kHz PCM but does not negotiate or validate protocol metadata.
- The `/home/xzhang/dev/voice-assist` worktree retains a pre-existing modified `uv.lock`; package source and lock consistency should be checked before release.
- No tracked secret was found. VoiceAssist can print configured API keys, and an ignored `voice-tools/.env` exists; secret contents were intentionally not inspected.

## 14. Final recommendation

**Which implementation should be the canonical reusable speech layer?**

`/home/xzhang/dev/voice-assist`, after the Phase 1 boundary hardening. It already has the correct repository/package direction and is substantially more reusable and testable than VoiceAssist.

**What valuable functionality, if any, should be extracted from the other implementation?**

Extract VoiceAssist's browser microphone-to-PCM WebSocket transport as an optional application integration, plus its buffering/disconnect behavior and wake-word/session policy as tested references. TTS/playback may become optional output adapters. Do not extract its retrieval, vehicle data, LLM configuration, generated files, or dead local-Whisper declarations into speech core.

**Should VoiceAssist become a separate repository?**

Yes, conservatively: create `bot0-voice-assistant`, extract and test the useful integrations first, then archive the remaining prototype there. Retain the current directory until that classification is complete.

**How should AgenticAICompass consume the canonical voice implementation?**

Through a declared, pinned `voice-tools` package dependency and its public injected API. Remove reliance on local editable installations and add fake-backend integration tests.

**Should the standalone voice assistant contain its own Whisper implementation?**

No. A local Whisper implementation, if required, should be an optional `voice-tools` transcription adapter shared by all applications.
