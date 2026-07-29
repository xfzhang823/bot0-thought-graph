# Excluded components

- **Frontend:** `my-react-app/`, `index.js`, and web assets belong to an application surface.
- **VoiceAssist:** audio, WebSocket, local Llama, vector, and socket deployment code is a separate product integration.
- **Runtime/generated data:** `input_output/`, thought-generation outputs, session state, memory, and checked-in artifacts are not package code.
- **Experiments:** evaluation/comparison experiments, sandboxes, demos, and manual runners require separate ownership and validation.
- **Backup files:** `*_backup.py`, `*_SAVED.py`, and `*_GOLD.py` are historical copies, not package modules.
- **Deployment-specific code:** legacy root services, startup scripts, FastAPI/TTS entry points, and machine-specific configuration remain application/deployment concerns.
