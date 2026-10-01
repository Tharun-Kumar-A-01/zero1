# PROJECT.md — Department Aptitude & Coding Practice Platform

> This document is the single source of truth for an AI coding agent building this project.
> Read it fully before writing any code. Where a decision is marked **[ASSUMPTION]**, it was made
> by the spec author to remove ambiguity — the agent should implement it as written unless the
> human operator overrides it. Where something is marked **[MUST VERIFY]**, the agent must confirm
> feasibility (e.g. package availability, Judge0 API shape) before relying on it.

---

## 1. Product Summary

A gamified daily-practice platform for a college department. Admins manage the system and roster.
Mentors (rotating weekly) upload one MCQ/aptitude question and one coding (LeetCode-style) problem
per day, sourced from a week's worth of content they prepare in advance. Students get one aptitude +
one coding challenge per day, in randomized order/variant per student, build streaks, earn reward
points and badges, and are tracked year-wise (batch-wise).

Core differentiators to build carefully:
- **Mentor rotation** automation (weekly handoff, no gaps, no double-assignment).
- **Per-student randomization** of question selection/order from the week's pool.
- **Local, backend-only LLM** for: Excel cell-range parsing, hardcoded-solution detection, and
  stress test-case generation — never exposed to end users directly.
- **Judge0-based execution** with strict resource/construct limits and stress testing.
- **Pixel-art visual theme** throughout (retro/8-bit aesthetic), fully custom design system.

---

## 2. Tech Stack (fixed — do not substitute without explicit approval)

| Layer | Choice |
|---|---|
| Frontend | Vue 3 (Composition API), Vue Router, Pinia, SCSS/Sass |
| Backend | Python, Flask, SQLAlchemy (ORM), Flask-JWT-Extended (or PyJWT + custom) |
| Database | PostgreSQL |
| Code execution | Self-hosted/local Judge0 instance (via its REST API) |
| Local AI | A small open-weights model run **locally** via Ollama or llama.cpp server, called only from the Flask backend over localhost/internal network |
| Async jobs | Celery + Redis (for async AI review, judge submissions, Excel import jobs) **[ASSUMPTION — see §9]** |
| File parsing | `openpyxl`/`pandas` for Excel, `python-magic` for MIME sniffing |

### 2.1 Local LLM specification

- Recommended model: a small **code-capable instruct model** such as `qwen2.5-coder:7b-instruct`
  or `codellama:7b-instruct`, served locally via **Ollama** (simplest local serving story) or
  `llama-cpp-python` with a GGUF quantized model. **[MUST VERIFY: pick based on host GPU/CPU
  constraints; default to a 7B Q4_K_M quantized GGUF for CPU-only hosts.]**
- The model is called **only** from backend service code (`ai_service.py` or similar). It is never
  given a public/user-facing endpoint. No route exists that forwards raw user text straight to the
  model without going through the sanitization + prompting layer in §8.
- All AI calls must:
  - Run through a single `LocalAIClient` wrapper class — no ad-hoc HTTP calls to the model scattered
    across the codebase.
  - Enforce a request timeout (e.g. 30–60s) and a token/character output cap.
  - Log prompt hash + response hash (not necessarily raw content) for audit, unless verbose debug
    logging is explicitly enabled.
  - Validate output against an expected JSON schema before using it (see §8.4). Never `eval()` or
    directly execute anything the model returns.

Required packages **[MUST VERIFY versions at implementation time]**:
```
ollama (python client) OR llama-cpp-python
openpyxl, pandas
python-magic
bleach (for stripping/sanitizing any AI-adjacent text before use)
unicodedata (stdlib, for normalization/invisible char stripping)
celery, redis
flask-jwt-extended
psycopg2-binary
marshmallow or pydantic (for schema validation of AI JSON outputs and API payloads)
```

---

## 3. Roles & Permissions

Three roles: **Admin**, **Mentor**, **Student**. A user can hold Admin + Mentor simultaneously
(admins can also be rotated as mentors) but Student is mutually exclusive from staff roles in this
version. **[ASSUMPTION]**

| Capability | Admin | Mentor | Student |
|---|:---:|:---:|:---:|
| Manage users / roles | ✅ | ❌ | ❌ |
| Bulk import students (Excel) | ✅ | ❌ | ❌ |
| Configure mentor rotation schedule | ✅ | ❌ | ❌ |
| Upload questions during their assigned week | ❌ | ✅ (own week only) | ❌ |
| Edit milestones / reward definitions | ✅ | ✅ | ❌ |
| View all students' progress (any year) | ✅ | ✅ (view only) | ❌ |
| Attempt daily challenges | ❌ | ❌ | ✅ |
| View own streak/points/badges | ❌ | ❌ | ✅ |
| Approve/override flagged (AI-suspected) submissions | ✅ | ✅ (for weeks they authored, or all — **decide via config flag**) | ❌ |

No self-registration exists for students (per your decision). Mentors and Admins are created by an
Admin directly (seed/admin panel), not via Excel import.

---

## 4. Data Model (PostgreSQL via SQLAlchemy)

Design as normalized relational tables. Suggested core entities (agent should refine field types,
but must preserve these relationships and constraints):

### 4.1 Users & Roles
- `users`: id, name, email (unique), password_hash, role (`admin`/`mentor`/`student`), is_active,
  created_at.
  - **Students additionally require**: `roll_number` (unique per academic year), `year_batch`
    (e.g. "2026", or admission year), `department`, `section` (nullable).
- `mentor_assignments`: id, user_id (FK→users, role must be mentor), week_start_date, week_end_date,
  status (`upcoming`/`active`/`completed`/`missed`), created_by_admin_id.
  - Constraint: no two active rows may overlap in date range (enforce at application layer + DB
    exclusion constraint if using `btree_gist`).

### 4.2 Question Bank
- `question_sets`: id, mentor_assignment_id (FK), week_start_date, status (`draft`/`published`/`archived`).
- `mcq_questions`: id, question_set_id (FK), prompt_text, options (JSONB array), correct_option_index,
  explanation (nullable), difficulty (`easy`/`medium`/`hard`), tags (JSONB/array), created_at.
- `coding_questions`: id, question_set_id (FK), title, word_problem_text (markdown), constraints_text,
  difficulty, allowed_languages (JSONB array, e.g. `["python","cpp","java"]`), time_limit_ms,
  memory_limit_kb, forbidden_constructs (JSONB — see §7.3), created_at.
- `coding_test_cases`: id, coding_question_id (FK), input, expected_output, is_sample (bool — shown
  to student vs hidden), is_stress_case (bool), source (`mentor_manual`/`mentor_csv`/`ai_generated`),
  weight (for partial scoring, optional).
- Constraint: every published `coding_questions` row must have **exactly 5** mentor-authored
  (non-stress) test cases before it can be published (per your spec). Stress cases are additional
  and separate.

### 4.3 Daily Assignment (the "one per day" mechanic)
- `daily_assignments`: id, student_id (FK), assignment_date, mcq_question_id (FK, nullable until
  resolved — see §5.2 for how selection happens), coding_question_id (FK), mcq_status
  (`pending`/`correct`/`incorrect`/`skipped`), coding_status
  (`pending`/`solved`/`attempted_unsolved`/`skipped`), created_at.
  - Unique constraint: (`student_id`, `assignment_date`) — a student gets exactly one row per day.

### 4.4 Submissions
- `mcq_submissions`: id, daily_assignment_id (FK), selected_option_index, is_correct, submitted_at.
- `code_submissions`: id, daily_assignment_id (FK), language, source_code, judge0_token,
  execution_status (`queued`/`running`/`passed`/`failed`/`error`/`timeout`),
  test_cases_passed_count, test_cases_total_count, runtime_ms, memory_kb,
  ai_review_status (`pending`/`clean`/`flagged`/`error`), ai_review_notes (text, nullable),
  ai_reviewed_at (nullable), submitted_at.
  - A student may resubmit code; decide (config) whether only the **latest** or **best** passing
    submission counts toward "solved" status. **[ASSUMPTION: best/first-passing submission counts;
    later resubmissions after a pass are allowed for practice but don't change streak.]**

### 4.5 Gamification
- `streaks`: id, student_id (FK, unique), current_streak, longest_streak, last_active_date,
  freeze_tokens (optional "streak freeze" credits, if implemented — see §7.5 edge cases).
- `milestones`: id, name, description, threshold_type (`streak_days`/`total_points`/`problems_solved`),
  threshold_value, reward_id (FK), created_by (mentor/admin), is_active.
- `rewards`: id, type (`points`/`badge`/`custom`), name, description, icon_asset_ref (pixel-art icon
  key), points_value (nullable, only for `points` type).
- `student_rewards`: id, student_id (FK), reward_id (FK), milestone_id (FK, nullable — null if
  manually granted), awarded_at.
- `points_ledger`: id, student_id (FK), delta, reason (`daily_mcq`/`daily_coding`/`milestone`/
  `manual_adjustment`), reference_id (nullable, polymorphic ref), created_at.
  - **Always compute total points as SUM(points_ledger.delta) for a student** — never store a
    mutable running total on the user row. This avoids drift/race-condition bugs.

### 4.6 Import Jobs (Excel + AI)
- `import_jobs`: id, admin_id (FK), original_filename, storage_path, status
  (`uploaded`/`parsing`/`ai_parsed`/`awaiting_confirmation`/`confirmed`/`committed`/`failed`),
  target_year_batch, ai_parse_result (JSONB — structured, schema-validated), error_log (nullable),
  created_at, committed_at.
  - Import is **never auto-committed**. The AI-parsed structure must be shown to the admin for
    confirmation before rows are written to `users`/`students`. See §8.2.

---

## 5. Core Feature Logic

### 5.1 Mentor Rotation
- Admin defines an ordered list of mentors and a rotation start date. Weeks run Mon–Sun
  **[ASSUMPTION — confirm with actual college week if different]**.
- A scheduled job (Celery beat, daily) checks: if today starts a new week and the outgoing mentor's
  `question_sets` for the week is not `published` with the required question count, mark the
  assignment `missed` and notify Admin — **do not silently skip students' daily assignment**; fall
  back to reusing a randomized past week's archived question set so students are never left with
  no challenge (§9 edge cases).
- Rotation order must be admin-editable (reorder, skip a mentor for one cycle, insert a new mentor)
  without breaking historical `mentor_assignments` records.

### 5.2 Daily Question Selection (randomization)
- Each mentor, during their week, uploads **enough MCQs and coding problems to cover 7 days**, e.g.
  a minimum pool (config value, default: 3–5 MCQs and 3–5 coding problems per day-equivalent, or a
  flat weekly pool of N≥7 of each — **decide and document the exact minimum in `config.py`,
  default N=7 of each so 1-per-day is guaranteed even with zero variation, but recommend N=14+ for
  actual randomization value**).
- Each night (scheduled job, e.g. 00:00 local time), for every active student, generate the next
  day's `daily_assignments` row by:
  1. Selecting one MCQ and one coding question from the **current week's published pool**,
     weighted to avoid repeats already served to that student this rotation cycle (track via a
     `served_questions` join table or a `NOT IN` query against the student's assignment history).
  2. If the pool is exhausted (more students-days than unique questions), allow repeats but never
     repeat the same question to the same student twice within a configurable window (default: the
     whole academic year).
  3. Persist the assignment **before** midnight rollover completes, so it's ready when students log
     in.
- This must be a **backend-generated, tamper-proof** assignment — students must never be able to
  choose or influence which question they get, and must not see other students' assignments.

### 5.3 Streak Logic — edge cases to explicitly handle
- A "day" is completed only when **both** the MCQ and the coding problem are correctly solved
  (config flag: `STREAK_REQUIRES_BOTH = True` by default — document if changed).
- Timezone: define a single canonical timezone for "day boundary" (e.g. Asia/Kolkata) — do not use
  each student's browser timezone for streak calculation, only for display.
- **Missed day = streak reset to 0**, unless a "streak freeze" token is available and the student
  (or system) applies it — if this feature is implemented, it must be explicit, not automatic, and
  logged.
- A student who joins mid-year should not be penalized for days before their `created_at` — streak
  eligibility starts from account creation date, not platform launch date.
- Late submission: if a student solves "today's" problem after midnight has passed (i.e. it's now
  technically a new day but they're finishing yesterday's assignment because they opened it before
  rollover), it must still count for the day it was **assigned**, not the day it was submitted,
  provided it's submitted before a grace cutoff (config, default 3 hours past midnight). After the
  grace cutoff, an unsolved assignment is finalized as missed.
- Retroactive edits (mentor edits a question after students already attempted it) must **never**
  retroactively change past correctness/streak outcomes.

### 5.4 Milestones & Rewards
- Mentors/Admins can create/edit milestones (threshold + reward). Editing a milestone's threshold
  must not retroactively revoke already-awarded rewards.
- A background job (or on-write trigger) checks, after each streak/points update, whether any
  milestone thresholds are newly crossed, and if so writes a `student_rewards` row (idempotent —
  never double-award the same milestone to the same student).
- Reward types: points (add to ledger), badge (icon/asset), or free-text custom reward (e.g.
  "certificate", "canteen coupon") — custom rewards are informational only, not auto-fulfilled by
  the system.

### 5.5 Year-wise Student Data
- All student-facing queries for progress/leaderboards must be scoped by `year_batch` by default,
  with an explicit admin-only "all years" / cross-year comparison view.
- Deleting/archiving a year batch must not cascade-delete `users` — use soft-delete/archive flags so
  historical data for alumni remains queryable by admins.

---

## 6. Excel Import + Local AI Parsing (Admin bulk student import)

### 6.1 Flow
1. Admin uploads an `.xlsx`/`.csv` file with unknown/inconsistent column layout (name, roll no,
   email, year, section, etc., possibly in any order, possibly with header rows not on row 1,
   merged cells, or extra metadata rows).
2. Backend runs `openpyxl`/`pandas` to extract raw grid data (cell values + row/col indices) —
   **do not send the raw binary file to the LLM**; send a sanitized, bounded textual/tabular
   representation (e.g. first N rows as a JSON grid) to the local model.
3. Local LLM is prompted (with a strict system prompt, see §8.1) to identify: header row location,
   which column maps to which known field (name/roll_number/email/year_batch/section), and the data
   row range — returning **only** a JSON object matching a fixed schema (§8.4).
4. Backend validates the JSON against the schema; if invalid, reject and ask admin to retry or map
   columns manually (always provide a manual-mapping fallback UI — the AI step must be an
   accelerator, never the only path).
5. Backend applies the mapping to build a preview table (parsed rows) and shows it to the Admin.
6. Admin **explicitly confirms** before any `users` rows are created (`import_jobs.status` moves
   `awaiting_confirmation` → `confirmed` → `committed`).

### 6.2 Edge cases to handle
- Duplicate roll numbers/emails within the same file, or against existing DB rows (same year vs
  different year) — flag as conflicts in the preview, don't silently overwrite.
- Rows with missing required fields — exclude from commit, list in a rejected-rows report.
- Non-UTF8 or mixed-encoding files — detect and normalize, or reject with a clear error.
- Extremely large files (e.g. >5000 rows) — process via async Celery job with progress status, not
  a blocking HTTP request.
- Malicious file content: formulas with external references, embedded macros (`.xlsm` should be
  rejected outright — only accept `.xlsx`/`.csv`), zip-bomb-style oversized compressed sheets — cap
  file size (config, default 10MB) and row/col count before any processing.

---

## 7. Judge0 Code Execution & Anti-Cheat

### 7.1 Execution flow
- Student submits code + selected language → backend validates language is in
  `coding_questions.allowed_languages` → backend runs **static pre-checks** (§7.3) before ever
  calling Judge0 → if pre-checks pass, submit to local Judge0 instance for each test case (5 mentor
  test cases first; stress cases run separately/afterward, see §7.4) → poll/callback for results →
  compute pass/fail → **show result to student immediately** → enqueue async AI review job
  (§7.5) → update `code_submissions.ai_review_status` when done; if flagged, surface a notice to
  mentor/admin dashboards (student's visible result does **not** change automatically — a human
  makes the final call on flagged submissions).

### 7.2 Judge0 configuration
- Use the local/self-hosted Judge0 instance's REST API (`/submissions`) with `wait=false` and either
  polling or Judge0's callback URL feature, so the Flask request thread isn't blocked.
- Enforce **per-submission resource limits** passed to Judge0: `cpu_time_limit`, `wall_time_limit`,
  `memory_limit`, `max_processes_and_or_threads` (see §7.3 — cap this low to block thread abuse),
  `enable_network` = false (submissions must never have network access).
- **[MUST VERIFY]** exact Judge0 API field names/version compatibility against the actual local
  instance version being deployed.

### 7.3 Forbidden constructs / static pre-check
Before sending code to Judge0, run a lightweight static check (language-aware, e.g. AST parsing for
Python via `ast` module, or a restricted regex/keyword blocklist for compiled languages where AST
isn't feasible) to reject or flag:
- Multi-threading / multiprocessing imports (`threading`, `multiprocessing`, `concurrent.futures`,
  Java `Thread`/`ExecutorService`, C++ `<thread>`, etc.) unless the specific problem explicitly
  allows/requires concurrency (rare — default deny).
- Direct filesystem access, network calls, subprocess/`exec`/`eval`/`system()` calls, environment
  variable access.
- Reading test data from anywhere other than stdin (i.e. no attempts to read hidden test files off
  disk, since Judge0 sandboxing should prevent this anyway — defense in depth).
- This check runs **per language** — maintain a small config table of banned identifiers/imports per
  supported language, extensible without code changes (e.g. a JSON/YAML rules file).
- If a submission is rejected at this stage, return a clear, specific error to the student
  (e.g. "Multithreading is not permitted for this problem") rather than a generic failure.

### 7.4 Stress testing
- In addition to the 5 mentor-authored test cases (correctness gate), coding problems can have a
  separate pool of **stress test cases** — either mentor-uploaded via CSV or AI-generated
  (local LLM, given the word problem + constraints, asked to produce large/edge-case inputs; the AI
  must also produce **expected outputs**, which for stress cases should be computed by running the
  mentor's own reference solution if one was provided, not just "trusted" from the LLM blindly —
  **[ASSUMPTION: require mentors to optionally provide a reference solution for AI-generated stress
  cases so expected outputs are verifiably correct, not LLM-hallucinated]**).
- Stress cases measure runtime/memory under larger inputs; results contribute to a "performance"
  metric shown to student/mentor but should **not** block a "solved" status if all 5 correctness
  cases pass — configurable (`STRESS_AFFECTS_PASS_STATUS`, default `False`).
- CSV stress-case format must be documented and validated on upload (columns: `input`, `expected_output`,
  optional `label`). Reject malformed CSVs with row-level error reporting.

### 7.5 AI Hardcoding / Shortcut Detection (async)
- After the Judge0 result is already shown to the student, enqueue a Celery job that sends the
  **word problem + the student's source code + the test case inputs/outputs (not the hidden ones the
  student never saw, to avoid ever leaking them into a prompt log unnecessarily beyond what's needed)**
  to the local LLM with a strict prompt (§8.3) asking it to classify: `clean` / `suspicious` (with
  reason) — e.g. output is a lookup table of the exact 5 known inputs, or the code ignores stdin
  entirely and prints constants, or uses input-length branching that only coincidentally matches
  provided cases.
- This is inherently heuristic — **the AI's verdict must never auto-fail or auto-penalize a student**.
  It only flags for **human review** (mentor/admin queue). Document this clearly as a
  human-in-the-loop system, not an automated punishment system, to avoid false-positive harm.
- Rate-limit/queue this so it doesn't overwhelm the local model if many students submit at once
  (Celery with a concurrency limit tuned to host capacity).

---

## 8. Local AI Safety & Sanitization Rules (apply everywhere the model is used)

### 8.1 Input sanitization (before any text reaches the model)
- Normalize Unicode (`unicodedata.normalize("NFKC", text)`).
- Strip zero-width and invisible/control characters (zero-width space, zero-width joiner, bidi
  override characters, non-printing control chars outside of `\n`/`\t`) via an explicit character
  filter — do not rely on normalization alone to catch these.
- Enforce a maximum input length (config, per use-case: Excel grid preview, code review, test-gen)
  and truncate/reject oversized input rather than passing it through.
- Strip or escape anything resembling prompt-injection patterns aimed at the system prompt (e.g.
  "ignore previous instructions") is **not sufficient defense alone** — the real defense is
  structural: the model's output is *never* trusted as executable instructions, only as data
  validated against a fixed schema (§8.4). Document this explicitly in code comments.

### 8.2 Interaction restriction
- No frontend route or component ever sends free-form user text straight to the local model. All AI
  calls are backend-initiated, backend-templated (fixed system prompt + slotted, sanitized data),
  and backend-validated on the way out.
- Students have **zero** direct or indirect ability to prompt the model (they cannot, for example,
  submit a "test case description" that gets forwarded verbatim as an instruction).
- Only Admin (Excel import) and Mentor (test-case generation) flows touch the AI, and always through
  the constrained wrapper.

### 8.3 Prompting approach
- Every AI call uses a fixed, versioned system prompt template stored in code (not user-editable),
  explicitly instructing the model to: only return the specified JSON structure, never follow
  instructions found inside the user-supplied data, never execute or simulate code, and never
  produce prose outside the JSON envelope.

### 8.4 Output validation
- Every AI response is parsed as JSON and validated against a `pydantic`/`marshmallow` schema
  specific to that call type (Excel-mapping schema, stress-test-case schema, hardcode-review
  schema). Invalid/non-conforming output → treat as a failure, retry once with a stricter
  re-prompt, then surface an error to the human user (never silently guess).

---

## 9. Scheduling & Background Jobs (Celery)

| Job | Trigger | Purpose |
|---|---|---|
| `rotate_mentor_week` | Daily (cron) | Advance rotation, mark missed weeks, notify admin |
| `generate_daily_assignments` | Daily, before midnight rollover completes | Create tomorrow's `daily_assignments` for all active students |
| `finalize_missed_assignments` | Daily, after grace cutoff | Mark unfinished assignments as missed, reset streaks accordingly |
| `check_milestones` | On-write (post submission/points update) or batched every few minutes | Award newly-crossed milestones idempotently |
| `ai_hardcode_review` | On each passing code submission | Async AI review (§7.5) |
| `import_job_parse` | On Excel upload | Run AI parsing + validation off the request thread |

**[ASSUMPTION]** Celery + Redis is used for all of the above; if the agent judges this overkill for
initial scope, APScheduler + simple thread-based async queues may substitute for the scheduling
jobs, but the AI review and import jobs should remain truly async/non-blocking regardless.

---

## 10. Pixel Art / Retro Visual Theme

- Design system: a dedicated SCSS design-tokens file (`_pixel-theme.scss`) defining a limited retro
  color palette, pixel-friendly fonts (e.g. a bitmap/pixel webfont), and consistent pixel-border /
  pixel-shadow mixins (no smooth border-radius or soft box-shadows — use stepped/pixelated borders,
  e.g. via `image-rendering: pixelated` on raster icon assets and hard-edged CSS clip-paths or
  border tricks for UI chrome).
- Icons/badges: stored as SVG or small PNG sprite sheets under `/src/assets/pixel/`, referenced by
  key (`icon_asset_ref` in `rewards` table) rather than hardcoded paths, so new badge art can be
  added without schema changes.
- Components to theme distinctly: streak flame/counter, badge showcase, leaderboard, daily challenge
  cards, code editor chrome (keep the actual code editor — e.g. CodeMirror/Monaco — functionally
  standard, just themed borders/chrome around it, not the text rendering itself).
- **[ASSUMPTION]** No specific existing pixel-art asset pack is licensed; agent should either
  generate simple original pixel-style SVG/CSS assets or clearly flag where a placeholder is used
  so the user can swap in real art later. Do not use copyrighted game assets (Mario, Pokémon, etc.).

---

## 11. API Surface (high-level — agent should flesh out full REST spec)

Group under `/api/v1/`:
- `auth/*` — login, refresh, logout (JWT, role in claims)
- `admin/students/*` — CRUD, bulk import (`POST /admin/students/import`, `GET /admin/students/import/:id/preview`, `POST /admin/students/import/:id/confirm`)
- `admin/mentors/*` — assign roles, manage rotation schedule
- `mentor/questions/*` — CRUD MCQ/coding questions for own active week, CSV/AI stress-case upload
- `mentor/milestones/*`, `mentor/rewards/*` — CRUD (shared with admin)
- `student/daily/*` — `GET /student/daily/today`, `POST /student/daily/mcq-submit`, `POST /student/daily/code-submit`
- `student/progress/*` — streak, points, badges, history
- `judge/*` — internal endpoints/webhooks for Judge0 callbacks (not public-facing beyond backend)
- `leaderboard/*` — year-scoped and (admin) cross-year

All mutating endpoints require JWT; role checks enforced via a decorator (`@requires_role("admin")`
etc.), not just frontend route guards — **frontend role checks are UX only, never a security
boundary.**

---

## 12. Security & Validation Checklist (non-negotiable)

- Passwords hashed with `bcrypt`/`argon2`, never stored/logged in plaintext.
- JWT access tokens short-lived; refresh token rotation implemented.
- All file uploads: type-sniffed (not trusted by extension alone), size-capped, virus/macro-stripped
  for Office files (reject `.xlsm`).
- All user-submitted code is treated as untrusted and only ever executed inside Judge0's sandbox —
  never `exec`/`eval`'d by the Flask app itself for any reason (including "quick preview" features).
- SQL access exclusively through SQLAlchemy ORM/parameterized queries — no raw string-interpolated
  SQL.
- Rate-limit submission endpoints per student (prevent spamming Judge0 or the AI review queue).
- CORS locked to the actual frontend origin(s), not `*`.
- Local AI model process should ideally run in its own container/user with no filesystem access
  beyond what's needed, and no outbound network access at all (it doesn't need the internet).

---

## 13. Edge Case Checklist (agent must explicitly handle/test each)

**Rotation & scheduling**
- Mentor added mid-cycle; mentor removed/deactivated mid-week; only one mentor exists total (rotation
  of size 1); a mentor's week ends without publishing enough questions.

**Assignment & randomization**
- Question pool smaller than 7 (must not crash — fall back per §5.1); student created mid-week
  (no assignment for days before creation); student deactivated then reactivated (resume streak or
  reset? — **[ASSUMPTION: reset streak on reactivation, log the gap]**); two students somehow get an
  identical MCQ+coding pairing (acceptable, not an error, as long as each pick is independently
  randomized — not required to be globally unique).

**Submissions**
- Student submits code but Judge0 instance is down/unreachable — queue and retry, show "pending" not
  a false failure.
- Student submits after the grace cutoff — reject gracefully with a clear "day closed" message, but
  still allow **practice-mode** resubmission that doesn't affect streak/points (**[ASSUMPTION]**
  practice mode should exist so learning isn't blocked, clearly labeled as not counting).
- Identical/near-identical code submitted by many students (plagiarism) — out of scope for AI
  hardcode-detection (that's a different problem: shortcut-detection vs plagiarism-detection); note
  this distinction explicitly in code comments so it isn't conflated. Plagiarism detection is **not**
  in this version's scope unless explicitly requested later.
- Test case with empty/edge input (empty array, zero, negative numbers, huge numbers, Unicode string
  input) — mentors should be encouraged (via UI hints) to include such cases among their 5, but the
  system doesn't auto-validate problem *quality*, only structural completeness (exactly 5 cases
  present).

**Milestones/rewards**
- Milestone threshold edited downward after some students already exceed it — award immediately on
  next recalculation (idempotency check prevents duplicate awards for students who'd already have
  qualified anyway under old threshold too).
- Two milestones with identical thresholds — both should independently trigger; no assumption of
  exclusivity.

**Excel import**
- File has students already existing in DB for a *different* year — treat as a new record (year is
  part of identity), not an update, unless roll_number+year matches exactly, in which case flag as a
  duplicate for admin decision (skip/update).
- AI mis-maps a column (e.g. confuses "email" and "roll_number" columns) — this is why preview +
  manual override before commit is mandatory (§6.1 step 5–6); never trust AI mapping blindly.

**AI review**
- Local model service is down/unresponsive when a review job runs — job should retry with backoff,
  and after N failures mark `ai_review_status = 'error'` and surface to admin, **never block the
  student's already-shown result**.
- Model returns malformed JSON — retry once with stricter prompt, then fail safe to `error` status
  (§8.4).

**Judge0**
- A submission exceeds memory/time limits — must be reported as a distinct status from "wrong
  answer" (e.g. `timeout`/`memory_exceeded`), shown clearly to the student, not lumped in with
  logic failures.
- Compilation errors (for compiled languages) — must be surfaced with the compiler's error text
  (sanitized/truncated), not a generic failure.

---

## 14. Explicit Assumptions Made By This Spec (review before build)

1. Week boundary = Monday–Sunday.
2. Streak requires **both** MCQ and coding solved same day (configurable).
3. Only the best/first passing code submission counts toward "solved"; further resubmits are
   practice-only.
4. Reactivating a deactivated student resets their streak.
5. AI-generated stress test expected-outputs are only trusted if derived from a mentor-provided
   reference solution, not purely LLM-generated expected outputs.
6. Celery + Redis for background/async work; substitutable with APScheduler for simpler scheduling
   jobs only, but async job architecture (import, AI review) should remain non-blocking regardless
   of scheduler choice.
7. No plagiarism detection (student-vs-student similarity) in this version — only per-submission
   hardcoding/shortcut detection against the problem's own I/O.
8. No student self-registration; admin-only bulk import via Excel.
9. Local LLM is used for structured/data tasks only, never given a chat-style interface reachable by
   end users.
10. Pixel art assets are original/placeholder — no licensed game IP.

If any of these don't match the actual intended behavior, update this section before or during
implementation — the agent should treat §14 as the first thing to double-check against evolving
requirements.
