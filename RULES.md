# RULES.md — Coding Standards & Operational Directives

> **TARGET AUDIENCE**: AI Coding Agents & Pair Programmers.
> **ENFORCEMENT**: Strict and non-negotiable across all development phases and tools.

---

## 1. Toolchain & Runtime Standards

### 1.1 Backend
- **Package Manager**: Use `uv` exclusively (`uv init`, `uv add`, `uv run`, `uv lock`). Never use raw `pip` or `poetry`.
- **Language & Runtime**: Python 3.12+ (or current active Python runtime).
- **Indentation**: Use **tabs** (`\t`) exclusively for indentation instead of spaces across all backend and frontend files.
- **Web Framework & Server**: Flask with blueprint-based modular structure, running under Gunicorn with Uvicorn workers (`uvicorn.workers.UvicornWorker`).
- **ORM & Database**: SQLAlchemy (ORM only with declarative base and typed models) on PostgreSQL. No raw string-interpolated SQL queries under any circumstances.

- **Cache & Message Broker**: **Valkey** (`valkey://`) exclusively (replacing Redis). Used for Celery broker/backend, atomic rate limiting, and distributed locking.
- **Authentication**: JWT-based authentication (Flask-JWT-Extended or PyJWT) with access/refresh token rotation and strict role-based decorators (`@requires_role`).

### 1.2 Frontend
- **Runtime & Package Manager**: `bun` exclusively (`bun add`, `bun run`, `bun test`). Never use `npm` or `yarn`.
- **Framework**: Vue 3 with Composition API (`<script setup lang="ts">`), Vue Router 4, and Pinia.
- **Component Library**: PrimeVue (v4+) using the **Aura** theme with default colors and built-in dark/light mode switching.
- **Icons**: PrimeIcons exclusively to maintain consistent icon styling across all components.

---

## 2. Concurrency, Race Condition Prevention & Rate Limiting

### 2.1 Two-Tier Rate Limiting Architecture
- **Tier 1 (Edge Proxy - Nginx)**:
  - Reverse proxy edge enforces burst and rapid request rate limiting per IP using `limit_req_zone` (e.g. general API 10r/s burst=20 nodelay; auth/submissions 2r/s burst=5).
  - Returns structured HTTP 429 Too Many Requests response.
- **Tier 2 (Application Layer - Flask + Valkey)**:
  - Backend enforces synchronous, atomic rate limits stored in **Valkey** (using atomic `INCR` + `EXPIRE` or Lua scripts).
  - Strict limits per student/user ID on submission endpoints (e.g. 5 submissions/minute) and auth endpoints (e.g. 5 login attempts/minute).
  - Rate limits must never block request threads asynchronously; state lookups and updates must be atomic.

### 2.2 Multithreading & Database Race Condition Prevention
- **Pessimistic Locking**: Use `SELECT ... FOR UPDATE` via SQLAlchemy (`with_for_update()`) on mutable concurrent records:
  - Daily assignment generation and status transitions.
  - Streak records and points ledger additions.
  - Mentor assignment state updates.
- **Valkey Distributed Locks**:
  - Use atomic Valkey locks (`SET key val NX EX timeout`) for scheduled jobs (midnight rollover, Celery beat tasks) so multiple server workers never duplicate operations.
- **Transaction Isolation**:
  - Run critical state changes inside explicit database transactions.
  - Ensure zero race conditions between reading and writing counters (e.g. streaks, points, attempt counts).

---

## 3. Containers & Deployment Architecture

### 3.1 Containerfiles & Compose
- **`Containerfile` / `Dockerfile`**:
  - Backend: Multi-stage, `uv`-based build, unprivileged user execution, healthcheck endpoint.
  - Frontend: Multi-stage build with `bun`, served by Nginx with edge rate-limiting and reverse proxying to backend `/api/`.
- **`docker-compose.yml` (Production / Full Stack)**:
  - Services: `postgres`, `valkey`, `judge0-server`, `judge0-workers`, `backend` (Gunicorn/Uvicorn), `celery-worker`, `celery-beat`, `frontend` (Nginx).
- **`docker-compose.dev.yml` (Development Infrastructure Only)**:
  - Runs **only** backing services: `postgres`, `valkey`, `judge0` (and dependencies).
  - No backend or frontend containers, allowing the developer to run `uv run ...` and `bun dev` on the host machine.

---

## 4. Type Safety & Determinism

### 4.1 Backend Type Annotations (100% Strict)
- **Every variable declaration** must have an explicit type annotation: `name: str = "value"`, `count: int = 0`, `items: list[str] = []`.
- **Every function and method** must have full type annotations for all parameters and an explicit return type:
  ```python
  def calculate_streak(
      student_id: int,
      current_date: datetime.date,
      assignment_status: DailyStatus
  ) -> StreakResult: ...
  ```
- **Type Checking Tool**: `mypy --strict` must pass without errors.
- **No `Any` Types**: Do not use `typing.Any` unless strictly interfacing with an untyped 3rd-party library, and isolate it immediately.

### 4.2 Deterministic Execution & Logic
- All business logic must be deterministic. Timezone operations must strictly use the canonical timezone (`Asia/Kolkata` or configured `SYSTEM_TIMEZONE`) via `zoneinfo.ZoneInfo`.
- Do not rely on server system local time or client-provided browser timestamps for business calculations (streaks, deadlines, rotation transitions).
- Random question selection must use cryptographically sound or explicitly seeded pseudo-random selection with documented exclusion tracking (`served_questions` join / query exclusion).

### 4.3 Frontend Type Safety
- Strict TypeScript (`<script setup lang="ts">`) across all Vue single-file components.
- All props, emits, and Pinia store states must be fully typed with explicit interfaces/types.
- `vue-tsc --noEmit` must pass without errors.

---

## 5. Input Sanitization & Security

### 5.1 Universal Sanitization Layer
- Never pass raw user-supplied input to LLMs, Judge0, or system utilities.
- **Text Normalization**:
  - Apply Unicode NFKC normalization: `unicodedata.normalize("NFKC", text)`.
  - Strip zero-width, non-printable, and bidirectional control characters.
  - Enforce strict character count / byte length limits per endpoint/input field.
- **HTML/XSS**: Sanitize rich text/markdown inputs using `bleach` with an explicit whitelist of safe tags and attributes.

### 5.2 LLM Invocation Security
- **Dual-Mode LLM Routing**:
  1. Check `.env` for primary configured LLM API (e.g. external provider API key & base URL).
  2. If absent or disabled, fall back to local Ollama model configured in the same `.env`.
- **No Direct User Prompting**: Users must NEVER have arbitrary prompt access to the LLM. All LLM calls are internal, system-templated, and bounded.
- **Prompt Injection Defense**:
  - Structural defense: System instructions must be fixed in code templates and isolated from user data.
  - LLM outputs must **only** be returned as structured JSON envelopes.
  - Every LLM response **must be validated** against a Pydantic schema before consumption.
  - If output validation fails, retry once with strict schema re-prompt; fail safe if still invalid. Never `eval()` LLM output.

### 5.3 Judge0 Code Execution Security
- **Static Pre-Checks**:
  - Run language-specific static AST analysis (for Python via `ast` module) and regex/keyword filters (for C++, Java) before queueing code to Judge0.
  - Disallow forbidden constructs: multithreading/multiprocessing (`threading`, `multiprocessing`, `concurrent.futures`, `Thread`), direct file system operations, network access, environment variable inspection, and OS command execution (`subprocess`, `os.system`, `fork`, `exec`, `eval`).
  - Provide clear, student-friendly error messages if forbidden constructs are detected (e.g. "Multithreading is not permitted for this problem").
- **Judge0 Sandbox Constraints**:
  - Explicitly pass strict resource limits on every submission: CPU time limit, wall time limit, memory limit, process/thread count ceiling.
  - Enforce `enable_network = false`.

---

## 6. Error Handling & Edge Cases

### 6.1 Explicit Exception Handling
- No bare `except:` or generic `except Exception: pass` blocks.
- Catch specific exceptions and log them with appropriate context.
- Return structured API error envelopes:
  ```json
  {
    "success": false,
    "error": {
      "code": "SPECIFIC_ERROR_CODE",
      "message": "Human-readable description of error.",
      "details": {}
    }
  }
  ```
- Never expose internal tracebacks, secret keys, or database internals to client responses.

### 6.2 Comprehensive Edge Cases
- Always handle:
  - Network timeouts and service unavailability (Judge0 down, LLM unreachable, Valkey down) with backoff and graceful fallback states.
  - Empty or boundary test inputs (zero, negative numbers, empty arrays, unicode strings).
  - Concurrent submissions or duplicate actions using database transactions, constraints, and idempotent job handlers.
  - Date/grace period edge cases (submissions at 23:59:59 vs 00:00:01 vs grace cutoff).

---

## 7. Testing Standards (Mandatory)

### 7.1 Backend Test Suite (`pytest`)
- **Unit Tests**:
  - Input sanitization functions (Unicode normalization, control character stripping, XSS filtering).
  - AST static analyzer (testing valid Python code, threading violations, file I/O violations, OS execution violations).
  - LLM response parser and Pydantic schema validation.
- **Integration Tests**:
  - JWT Authentication, refresh token rotation, and role-based permissions.
  - Submission pipeline: static check -> Judge0 simulation -> score update.
  - Valkey rate-limiting verification (verifying 429 on exceeding thresholds).
- **Concurrency & Race Condition Tests**:
  - Multi-threaded test runner executing concurrent submissions to verify database row locking (`with_for_update()`) and idempotent daily assignments.
- **Edge Case Tests**:
  - Submissions during midnight rollover, boundary inputs, malformed Excel import sheets.

### 7.2 Frontend Test Suite (`vitest` + `@vue/test-utils`)
- **Component Tests**:
  - PrimeVue Aura component rendering, dark/light theme switcher.
  - Form validation on login and question authoring forms.
  - Daily challenge card status transitions (pending, solved, failed).
- **Store & Integration Tests**:
  - Pinia auth store, token persistence, and axios/fetch interceptor token refresh.
  - Rate-limit error (HTTP 429) visual feedback handling.

---

## 8. Code Quality, Linters & Deprecation Policy

### 8.1 Linters & Formatters
- **Backend**:
  - `ruff check .` for linting (clean, zero warnings).
  - `ruff format .` for code formatting.
  - `mypy --strict .` for type integrity.
- **Frontend**:
  - `eslint . --ext .vue,.ts` for linting.
  - `prettier --check .` for formatting.
  - `bun run type-check` (`vue-tsc --noEmit`) for Vue TypeScript checks.

### 8.2 Deprecation & Modern Syntax Rules
- **No Deprecated Libraries/APIs**:
  - Use modern SQLAlchemy 2.0+ syntax (`select()`, `session.scalars()`, `Mapped[...]`, `mapped_column(...)`). Do not use legacy Query APIs (`session.query()`).
  - Use Pydantic V2 syntax (`model_validate`, `field_validator`). Do not use V1 methods (`parse_obj`, `validator`).
  - Use modern standard library features (e.g., `pathlib.Path`, `zoneinfo.ZoneInfo`, `dataclasses`, built-in generics `list[str]`, `dict[str, int]`).
  - Frontend: Use Vue 3 `<script setup lang="ts">` syntax. Do not use the legacy Vue 2 Options API.
  - Frontend: PrimeVue 4+ syntax and component conventions.
- **Imports**: Clean, grouped imports (Standard Library -> Third-party -> Local application modules). No wildcard imports (`from module import *`).

---

## 9. Development Workflow Rules for AI Agents

1. **Rule Zero**: Before completing any task, run both backend linters (`ruff`, `mypy`) and frontend linters/type checks (`eslint`, `vue-tsc`). Code must be 100% clean.
2. **Deterministic Output**: Never generate placeholder code (`# TODO: implement later`) in core business logic.
3. **Auditability**: Document API endpoints, database schemas, and edge case assumptions clearly.

