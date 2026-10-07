# Zero1 — Department Aptitude & Coding Practice Platform

A gamified daily-practice platform for a college department. A rotating weekly mentor uploads one MCQ and one coding problem per day; students get a randomized daily pair, build streaks, and earn points and badges. Code is judged by a self-hosted Judge0 instance behind static anti-cheat checks, with an async, human-in-the-loop AI review layer for suspected shortcut/hardcoded solutions.

> **Status: early prototype.** Core backend services, data models and the API surface are implemented; the pixel-art UI theme and the full reward/milestone system are still in progress.

## Why this exists

Most coding-practice tools either run everything client-side (no real anti-cheat) or hand code review entirely to an AI (no human in the loop). This project is built around two constraints instead:

- **Students must never be able to choose or see what they're asked** — question selection is backend-generated and tamper-proof, with per-student randomization and repeat-avoidance tracked against each student's assignment history.
- **AI never makes the final call.** A local/self-hosted LLM flags suspected hardcoded or shortcut solutions asynchronously, after the student has already seen their Judge0 result — it only raises a flag for a mentor or admin to review, and it never auto-fails a submission.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python, Flask (blueprints), SQLAlchemy 2.0 (typed models), Gunicorn + Uvicorn workers |
| Frontend | Vue 3 (Composition API, `<script setup lang="ts">`), Vue Router, Pinia, PrimeVue (Aura theme) |
| Database | PostgreSQL |
| Cache / broker / locks | Valkey (Celery broker + backend, atomic rate limiting, distributed locks) |
| Async jobs | Celery (beat + workers) |
| Code execution | Self-hosted Judge0 |
| AI | Dual-mode: external LLM API if configured, else local Ollama model — never exposed to a user-facing endpoint |
| Package managers | `uv` (backend), `bun` (frontend) — enforced, no `pip`/`npm` |
| Auth | JWT (access + refresh rotation), role-based route decorators |

## What's implemented

**Backend** (`backend/app/`)
- `api/` — `auth`, `admin`, `mentor`, `student`, `health` blueprints (~55 routes across them)
- `models/` — users/roles, mentor rotation assignments, question bank (MCQ + coding + test cases), daily assignments, submissions, gamification (streaks, milestones, rewards, points ledger), import jobs
- `services/`
  - `judge0_client.py` — submission encoding/decoding and language-ID mapping for the Judge0 REST API
  - `code_analyzer.py` — static pre-execution checks: AST-based analysis for Python (banned modules/calls like `os`, `subprocess`, `eval`, `exec`), regex-based checks for C++/Java forbidden constructs (threads, `fork`, `system`, sockets)
  - `code_boilerplate.py`, `code_harness.py` — per-language boilerplate and test harness generation
  - `rotation_service.py` — resolves the active weekly question set, with fallback to the most recent published set if a mentor's week is incomplete
  - `streak_service.py` — streak/points evaluation; totals are always computed as `SUM(points_ledger.delta)` rather than stored as a mutable counter, to avoid race-condition drift
  - `sanitizer.py` — Unicode NFKC normalization, invisible/control-character stripping, `bleach`-based HTML allowlisting for any text that reaches the AI layer
  - `rate_limiter.py`, `lock_service.py` — Valkey-backed atomic rate limits and distributed locks (`SET NX EX`) so scheduled jobs never double-run across workers
  - `ai_client.py` — the LLM routing/wrapper layer

**Frontend** (`frontend/src/`)
- Role-specific views: `AdminView`, `MentorView`, `StudentView`, plus `LeaderboardView`, `ProfileView`, `LoginView`, `CodingWorkspaceView`
- Component sets per role: admin (roster import, mentor schedule, user directory), mentor (MCQ/coding pools, AI stress-test dialog, flagged-submissions queue, rotation overview), student (code editor, test case console, challenge cards, streak tracker, badges)
- Pinia auth store with token persistence; typed API service layer
- Unit tests (Vitest + Vue Test Utils) for key components, the auth store and the API layer

**Infrastructure**
- Multi-stage `Containerfile`s for backend (`uv`-based) and frontend (`bun`-based, served by Nginx)
- `docker-compose.yml` — full stack: Postgres, Valkey, Judge0 server + workers, backend, Celery worker + beat, frontend
- `docker-compose.dev.yml` — backing services only, for running the backend/frontend on the host during development
- Two-tier rate limiting: Nginx edge limits per IP, Valkey-backed atomic per-user limits in the app layer

## Not yet built

- Pixel-art visual theme (currently a standard PrimeVue Aura UI)
- Full milestone/reward UI and badge issuance flow
- Excel bulk-import AI column mapping (model-assisted parsing with admin confirmation)
- End-to-end integration tests for the full submission → Judge0 → AI-review pipeline

## Getting started (development)

```bash
# Backing services only (Postgres, Valkey, Judge0)
docker compose -f docker-compose.dev.yml up -d

# Backend
cd backend
uv sync
uv run flask run

# Frontend
cd frontend
bun install
bun dev
```

Copy `.env.example` to `.env` and fill in secrets before running. Key variables: `DATABASE_URL`, `VALKEY_URL`, `JUDGE0_URL`, and either `LLM_API_KEY`/`LLM_BASE_URL` or the `OLLAMA_*` fallback pair.

## Testing & linting

```bash
# Backend
cd backend
ruff check .
mypy --strict .
pytest

# Frontend
cd frontend
bun lint
bun run type-check
bun test:unit
```

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Flask blueprints (auth, admin, mentor, student, health)
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Judge0, AI, anti-cheat, rotation, streaks, rate limiting, locks
│   └── tests/            # unit, integration, concurrency, edge-case tests
├── frontend/
│   └── src/
│       ├── components/   # admin/, mentor/, student/, leaderboard/, common/
│       ├── views/
│       ├── stores/       # Pinia
│       └── services/     # API client
├── docker-compose.yml
└── docker-compose.dev.yml
```
