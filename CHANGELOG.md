# Changelog

All notable changes to this project are documented here; see `docs/MASTER_AUDIT.md` and `docs/CLEANUP_PLAN.md` for the full audit and cleanup trail.

## [Unreleased] — 2026-08-10

### Fixed
- `InterviewEngine`: conversation logs passed to follow-up generation are now chronologically interleaved per turn (previously all questions before all answers).
- `InterviewEngine`: topic exhaustion now completes the session when no further topics remain (previously it kept asking follow-ups forever).
- `InterviewEngine`: the topic-exhaustion policy is reset per session (no keyword leakage across sessions).

### Added
- Regression tests for the three interview fixes (`tests/test_interview_orchestration.py`, 8 tests).
- Test coverage for `providers.default_model()` + `<PROVIDER>_MODEL` env override, `interview/state.py`, `orchestration/coordinator.py`, `orchestration/policies.py`, `thought_generation/reader.py` surface, and `thought_generation/ranking.py` edge cases (8 new tests).

### Changed
- Removed stub-only `tests/unit/` and `tests/integration/` packages, the empty `sandbox/` directory, and build artifacts (`dist/`, `build/`); removed the `repro_interview.py` debug artifact.

## 2026-08-08

### Added
- `ProgressionType` enum (`implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, `prerequisite_dependency`) with typed defaults in vertical expansion and the concept-first façade.
- Concept-first façade: canonical `topic=` parameter (legacy `concept=` retained as alias), `progression_type=` on `expand_subtopic()` and `generate_thought_graph()`, provider-name construction (`ThoughtGraphEngine(provider="deepseek", ...)`), and per-provider default models via `providers.default_model()` with a `<PROVIDER>_MODEL` environment override.
- Google Gemini and DeepSeek OpenAI-compatible provider adapters (sync + async), `create_provider()` factory, and `reasoning_content` passthrough.

### Changed
- Migrated pydantic class-based `Config` to `ConfigDict` (no more `PydanticDeprecatedSince20` warnings).
- README.md rewritten and expanded (provider matrix, concept-first workflow, typed API, persistence, examples).

### Notes
- Commit lineage: `36914401` (providers) … `08caa9cd` (ProgressionType); see `docs/MASTER_AUDIT.md`.
