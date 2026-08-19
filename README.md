# CampusWise AI

**AI-Powered Course, Professor & Semester Planning Assistant**

## Problem

Students juggle disconnected tools — course catalogs, professor rating sites, grade-distribution spreadsheets, PDF syllabi, degree audits — to answer one question: *what should I take next semester, from whom, and when?*

## Solution

CampusWise AI is an AI Academic Decision Intelligence Platform. A student describes what they want in plain language; the system parses that into structured hard constraints and soft preferences, retrieves verified course/professor/grade/syllabus data, ranks and explains matches, and generates optimized semester schedules — without ever letting the AI invent a fact.

See [`docs/architecture-proposal.md`](docs/architecture-proposal.md) for the full product/system/AI/database/API architecture and phased roadmap.

## Status

**Phase 1 — Foundation** is complete: monorepo scaffold, FastAPI backend with health checks and basic auth, Next.js frontend shell, PostgreSQL (pgvector-ready) + Redis via Docker Compose, Alembic migrations, and a passing test suite.

**Phase 2 — University Data** is complete: core data model (universities, departments, terms, buildings/rooms, courses + topic tags, professors + aggregate ratings, sections + meeting times, historical grade records), a synthetic sample dataset (20 courses, 15 professors, 40 sections, 3 terms of grade history for a fictional "Northlake University"), deterministic grade-distribution analytics, and search APIs (`/courses/search` keyword+topic search, `/professors?min_rating=`, `/professors/{id}/grades`, `/sections?delivery_mode=`).

**Phase 3 — Course/Professor UI** is complete: server-rendered course search (`/courses`, filter by keyword/topic), course detail pages with section listings and meeting times (`/courses/[id]`), professor search (`/professors`, filter by minimum rating), professor profile pages with a historical grade-distribution chart (`/professors/[id]`), and friendly 404s for missing/malformed IDs. Filtering uses plain GET forms server-side — no client-side state library yet, since that lands with Phase 4's conversational AI search.

**Phase 4 — AI Search** is complete: `POST /api/v1/ai/search` takes a natural-language query and returns structured hard constraints + soft preferences (delivery mode, time window, excluded days, minimum professor rating, level) plus matching courses and professors. A `RequirementParserAgent` tries an LLM (Claude, via `ANTHROPIC_API_KEY`) first for open-ended phrasing, and falls back to a deterministic regex-based parser when no key is configured or the call fails — so search keeps working offline, in CI, and in local dev without any API key. The LLM never invents course/professor/grade facts; it only restructures the student's own words, and every unverifiable requirement (e.g. exam format — no syllabus data exists yet) is surfaced as an explicit note rather than a claim.

**Phase 5 — Recommendation Engine** is complete: `POST /api/v1/recommendations/courses` runs the full pipeline — parse query → discover candidate courses → gather sections in the active planning term → deterministic hard-constraint filtering (delivery mode, time window, excluded days, minimum professor rating — a missing rating is treated as failing the constraint, never assumed to pass) → per-section feature scoring (professor rating, historical grades, delivery-mode preference, grading ease, campus days) → an adaptive Fit Score (0–100) that renormalizes weights across only the dimensions that are both requested and backed by real data → ranked, explained results (`matched` / `not_matched` / `missing_info`, the last always flagging that exam format, reviews, and workload data don't exist yet). Excluded-candidate counts are surfaced in `notes` (e.g. "2 section(s) excluded: professor rating below your threshold") so students know which requirement narrowed the results.

**Phase 6 — Syllabus RAG** is complete: `POST /api/v1/rag/query` answers syllabus questions with citations. Pipeline: PDF/text loading → paragraph-aware chunking → embeddings (Voyage AI when `VOYAGE_API_KEY` is set, otherwise a deterministic offline hashing fallback — same fallback pattern as Phase 4's parser) → storage in Postgres via `pgvector` (with a portable JSON fallback for the SQLite test database) → hybrid retrieval (dense cosine similarity + lexical term-overlap, combined by Reciprocal Rank Fusion) → reranking (Voyage rerank API when configured, else a heuristic) → an LLM-synthesized answer (Claude) that treats retrieved excerpts strictly as untrusted data, never instructions, with a deterministic excerpt-citation fallback when no `ANTHROPIC_API_KEY` is set. Every answer carries citations (course, professor, term, source document, excerpt) and a confidence level; when no syllabus exists for a course, the response says so explicitly instead of guessing. 10 synthetic syllabus documents (`scripts/seed_syllabi.py`) cover a range of exam formats and grading structures for demo purposes.

**Phase 7 — Exam Intelligence** is complete: every syllabus ingested (Phase 6) now also gets structured, provenance-tagged assessment metadata extracted from it — midterm/final exam format (online/in-person/take-home/none), open- vs. closed-book, proctoring tool, group/individual projects, presentations, quizzes, attendance policy, late policy, and a component→weight-percentage breakdown. An LLM extractor (Claude tool-use) is the primary path, with a deterministic regex extractor as the offline fallback — same pattern used throughout the AI layer. `GET /api/v1/assessment/course/{id}` and `GET /api/v1/assessment/professor/{id}` expose it directly, and the Recommendation Engine's `exam_preference` dimension now uses real extracted data instead of always reporting "not available": a student asking for "online exams" gets sections scored and explained against the actual syllabus-derived exam format, with the source document cited in the explanation. Fixed two real bugs surfaced by live verification: the parser was misreading "online exams" as a course-delivery-mode requirement (would incorrectly exclude in-person-delivery sections whose *exams* happened to be online), and the requirement parser's fallback still claimed exam data "isn't available yet" from before this phase existed.

**Phase 8 — Schedule Optimization** is complete: `POST /api/v1/schedule/generate` builds real semester schedules with Google OR-Tools CP-SAT — hard constraints (no time conflicts, at most one section per course, total credits within the requested range, plus every Phase 5 hard constraint already applied upstream) are never violated; which combination is "best" is purely an objective function, computed once per named strategy against the same Fit Score data the Recommendation Engine already produced, so the optimizer never invents its own quality signal. Five strategies run per request — Best Overall, Best Professors, Fewest Campus Days, Best Historical Grades, Online-Heavy — each returned independently (`null` if infeasible, with a note explaining why). `POST /api/v1/schedule/validate` runs the same deterministic conflict detector standalone (time overlaps, and a <15-minute-transition-time warning for tight back-to-back classes) against any list of section ids. The frontend gained an interactive **Schedule Builder** page (`/schedule`) — a client-side form that calls the backend directly from the browser, with tabs across the five strategies and a from-scratch weekly calendar component (no charting library) rendering each schedule's meeting blocks by day/time.

**Phase 9 — Degree Planning** is complete: `degree_programs` with named requirement groups (Core/Electives/Capstone, each needing some count of courses from an eligible list) and an AND/OR `course_prerequisites` graph — "Course C requires A AND (B OR D)" is represented as prerequisite rows sharing an OR'd `group_number`, with different group numbers AND'd together, checked by a pure deterministic `prerequisite_engine` (never an LLM). Students (the existing `users` table from Phase 1) can enroll in a degree program, mark courses completed, and get real progress (`GET /degree/progress`) and next-semester suggestions (`GET /degree/next-courses`) — sorted eligible-and-offered-this-term first, with plain-English missing-prerequisite explanations (e.g. `"CS 3345 or CS 4375"`) for anything not yet eligible. `GET /courses/{id}/prerequisites` (public) and `GET /courses/{id}/eligibility` (per-student) expose the same graph directly. 3 synthetic degree programs with a real prerequisite chain (`scripts/seed_degrees.py`) demonstrate both AND and OR logic across the seeded course catalog.

**Phase 10 — Production Hardening** is complete:
- **Caching**: Redis cache-aside on the two endpoints the brief specifically calls out as expensive/repeated (course search, grade distributions), with a 60s TTL and no invalidation-on-write (acceptable for slowly-changing catalog data; documented as a scaling point). Caching degrades gracefully to "just compute it" if Redis is unreachable — it's an optimization, never a dependency.
- **Rate limiting**: per-IP limits (slowapi), a global default plus a stricter `10/minute` on `/auth/login` and `/auth/register` to blunt credential-stuffing/enumeration attempts.
- **Observability**: every request gets a short request id, logged with method/path/status/duration and echoed back as an `X-Request-ID` response header for client-to-server error correlation.
- **Error handling**: a global exception handler guarantees no unhandled exception ever reaches a client as a raw traceback — it's logged in full server-side and returned as a clean `{"error_code": "internal_error", ...}` body.
- **Evaluation**: `scripts/evaluate_rag.py` is a small, real, runnable regression harness — hit@k against known-answerable questions and abstention-accuracy against known-unanswerable ones, run against the actual retrieval pipeline and seeded syllabi.
- **CI/CD**: `.github/workflows/ci.yml` — backend lint (ruff) + tests (pytest, currently 115 passing at 93% coverage) + advisory type-check (mypy) and dependency-vulnerability scan (pip-audit); frontend lint + type-check + build; then a Docker build of both images. Mypy and pip-audit are advisory (`continue-on-error`) since a fast-moving AI SDK's type stubs and OR-Tools' generated bindings currently produce false positives that don't reflect real runtime bugs — verified by extensive live testing throughout every phase.
- Along the way, fixed every *real* mypy finding in first-party code (a tuple-type narrowing issue in the assessment extractor, loosely-typed ranking caches, a Voyage embeddings return-type mismatch) and every ruff finding (mostly `F821` false positives from SQLAlchemy's string-based relationship type hints, resolved properly via `TYPE_CHECKING` imports rather than suppressed) — and caught a real test-suite fragility bug in the process: the rate limiter's in-memory store persisted across the whole pytest session, and the test suite was making exactly 10 auth calls against a 10/minute limit — one more test would have started failing tests unrelated to rate limiting. Fixed by resetting the limiter per test, with a regression test locking in the correct isolated behavior.

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL (pgvector), Redis
- **Embeddings/Rerank (from Phase 6 onward):** Voyage AI (`voyage-3-lite` / `rerank-2-lite`), with a dependency-free deterministic fallback when no key is configured
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS
- **AI (from Phase 4 onward):** LangGraph, LangChain, Anthropic Claude
- **Optimization (from Phase 8 onward):** Google OR-Tools (CP-SAT)
- **Infra:** Docker, Docker Compose

## Project Structure

```text
campuswise-ai/
├── frontend/     Next.js app (App Router, TypeScript, Tailwind)
├── backend/      FastAPI app (api, agents, models, schemas, services, ...)
├── data/         raw / processed / sample datasets
├── docs/         architecture, database, AI system, API docs
├── infrastructure/
├── scripts/
└── docker-compose.yml
```

## Getting Started

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (docs at `/docs`)
- Postgres: localhost:5432 (`campuswise` / `campuswise`)
- Redis: localhost:6379

### Option B — Run backend and frontend locally

**Backend**

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # or: source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env       # point DATABASE_URL at a running Postgres instance
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (requires Node.js 20+)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example`. Never commit real secrets — `.env` is gitignored; only `.env.example` files are tracked.

## Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Testing

```bash
cd backend
pytest -q                              # 115 tests, ~93% coverage
ruff check .                           # lint
mypy app --ignore-missing-imports      # type check (advisory — see CI notes below)
```

Backend tests run against an in-memory SQLite database via `tests/conftest.py`, so no running Postgres instance is required to test application logic. The rate limiter's storage is reset per test (see `tests/conftest.py`) so tests never accumulate rate-limit state across the session.

```bash
cd frontend
npm run lint
npm run build   # also runs Next.js's TypeScript type check
```

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`: backend lint + tests + advisory type-check/dependency-scan, frontend lint + type-check + build, then a Docker build of both images. See `docs/architecture-proposal.md` for the full pipeline rationale.

## Manual Verification (Phase 1)

1. Start the stack (`docker compose up --build`, or run backend + frontend locally as above).
2. Visit `http://localhost:8000/api/v1/health` — expect `{"status": "ok", ...}`.
3. Visit `http://localhost:8000/api/v1/health/ready` — expect `"database": "ok"` (requires Postgres reachable).
4. Visit `http://localhost:3000` — the CampusWise AI landing page should show "Backend status: connected".
5. `POST http://localhost:8000/api/v1/auth/register` with `{"email": "...", "password": "..."}`, then `POST /api/v1/auth/login` with the same credentials to receive a JWT, then `GET /api/v1/auth/me` with `Authorization: Bearer <token>`.

## Manual Verification (Phase 2)

1. Apply migrations and seed the sample dataset:
   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python scripts/seed_data.py
   ```
   (Locally without Docker: `alembic upgrade head && python scripts/seed_data.py` from `backend/`.)
2. `GET /api/v1/courses/search?q=python` — expect several courses tagged with the "python" topic (e.g. `CS 1336`, `CS 4375`, `BUSN 4325`).
3. `GET /api/v1/professors?min_rating=4.0` — expect only professors whose aggregate rating is at or above 4.0.
4. `GET /api/v1/professors/{id}/grades` — expect a computed grade distribution (mean GPA, A/B/C/D-F percentages, withdrawal %) with the disclaimer that historical data does not guarantee future outcomes.
5. `GET /api/v1/sections?delivery_mode=online` — expect only online sections, each with nested course/professor/term/meeting details.
6. `GET /api/v1/terms` — expect three terms (Fall 2025, Spring 2026, Fall 2026), with Fall 2026 flagged `is_active_for_planning: true`.

## Manual Verification (Phase 3)

With the stack running and seed data loaded:

1. Visit `http://localhost:3000/courses` and search "python" — expect `CS 1336`, `CS 4375`, `CS 4395`, `STAT 4351`, `STAT 4382`, and `BUSN 4325`.
2. Click into a course — expect its sections listed with day/time, delivery mode, seats, and a link to the assigned professor.
3. Visit `http://localhost:3000/professors` and filter by "4.5+" rating — expect only professors at or above that threshold.
4. Click into a professor — expect overall/teaching/difficulty ratings, would-take-again %, and a grade-distribution bar chart with mean GPA and A/B/C/D-F range percentages.
5. Visit a course or professor URL with a made-up ID (e.g. `/courses/not-a-real-id`) — expect a friendly 404 page, not a crash.

## Manual Verification (Phase 4)

With the stack running and seed data loaded (no `ANTHROPIC_API_KEY` needed to test the fallback path):

```bash
curl -X POST http://localhost:8000/api/v1/ai/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Show online graduate courses about python with professor rating above 4"}'
```

Expect `parsed.topic` = `"python"`, `parsed.hard_constraints.delivery_modes` = `["online"]`, `level` = `"graduate"`, `minimum_professor_rating` = `4.0`, `parsed.parser_source` = `"rule_based"` (or `"llm"` if `ANTHROPIC_API_KEY` is set), and `courses`/`professors` filtered accordingly. Try the other demo phrasings from the product brief (§57) — "I need a class after 4 PM", "no Friday meetings", "I want an online course with online exams" — and check the `notes` field surfaces anything the platform can't verify yet (e.g. exam format).

## Manual Verification (Phase 5)

With the stack running and seed data loaded:

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/courses \
  -H "Content-Type: application/json" \
  -d '{"query": "I want a python course, no Friday classes, and a professor rated above 4"}'
```

1. Expect only sections with no Friday meetings and a professor rating ≥ 4.0 in `recommendations`, sorted by `fit_score` descending.
2. Each recommendation's `score_breakdown` should only include dimensions with real backing data (e.g. `professor_rating`, `historical_grades`) — never a fabricated number for something unverifiable.
3. `missing_info` should always mention exam format, reviews, and workload as not yet available.
4. Raise the rating bar past what any seeded professor has (e.g. "professor rated above 4.8") — expect an empty `recommendations` list and a `notes` entry like `"N section(s) excluded: professor rating below your threshold."`, so the student learns which requirement is too strict instead of just seeing nothing.

## Manual Verification (Phase 6)

With the stack running and both seed scripts run (`python scripts/seed_data.py` then `python scripts/seed_syllabi.py`):

```bash
# Find a course id, e.g. for CS 4375
curl "http://localhost:8000/api/v1/courses/search?q=machine%20learning"

curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is the final exam online?", "course_id": "<course-id-from-above>"}'
```

1. Expect `citations` pointing at `CS4375_Fall2025.pdf` with an excerpt containing "administered online... proctored via Honorlock", and `confidence` of `medium` or `high`.
2. Try "Does this course have a group project?" against `CS 4395` (Natural Language Processing) — expect the team-research-project excerpt to surface.
3. Query a course with no seeded syllabus (e.g. Calculus II) — expect `"No syllabus information is available for this course yet."`, `confidence: "none"`, and an empty `citations` list, not a guessed answer.
4. `answer_source` will read `"excerpt_only"` without `ANTHROPIC_API_KEY` set (a literal citation, no LLM synthesis) or `"llm"` with a key configured.

## Manual Verification (Phase 7)

With the stack running and both seed scripts run:

```bash
# Find CS 4347's id, then:
curl "http://localhost:8000/api/v1/assessment/course/<course-id>"
```

1. Expect `midterm_format` and `final_format` both `"online"`, both `*_open_book: true`, and a `weights` breakdown like `{"midterm exam": 20.0, "final exam": 25.0, ...}` for CS 4347 (Database Systems / Dr. Samuel Okafor).
2. Run a recommendation query that combines a topic with an exam preference:
   ```bash
   curl -X POST http://localhost:8000/api/v1/recommendations/courses \
     -H "Content-Type: application/json" \
     -d '{"query": "database course with online exams"}'
   ```
   Expect `parsed.hard_constraints.delivery_modes` to be `null` (not `["online"]"` — "online exams" must not be misread as a delivery-mode requirement) and `parsed.soft_preferences.prefer_online_exams: true`. The returned recommendation for CS 4347 should show `score_breakdown.exam_preference: 100.0` and a `matched` entry citing the syllabus source document.
3. Query `/assessment/course/{id}` for a course with no ingested syllabus — expect an empty list, not an error or a guess.

## Manual Verification (Phase 8)

With the stack running and seed data loaded:

```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "no Friday classes", "min_credits": 12, "max_credits": 15}'
```

1. Expect `schedules` to contain all 5 strategy keys (`best_overall`, `best_professors`, `fewest_campus_days`, `best_grades`, `online_heavy`); each non-null one should total between 12–15 credits and contain zero Friday meetings.
2. Compare `fewest_campus_days` against `best_overall` — it should show fewer distinct `campus_days` (often 0 if an all-online combination is reachable within the credit range).
3. Take the `id`s from any generated schedule's `sections` and POST them to `/api/v1/schedule/validate` — expect `is_valid: true` and an empty `conflicts` list (a generated schedule should never self-conflict).
4. Manually pick two sections that meet at the same day/time (check `/api/v1/sections?term_id=...`) and validate them together — expect a `time_overlap` conflict with a plain-English explanation.
5. Set `min_credits`/`max_credits` to an unreachable range (e.g. `40`–`45`) — expect every strategy to return `null` and a `notes` entry explaining no feasible schedule was found.
6. Visit `http://localhost:3000/schedule`, enter a query like "no Friday classes, prefer online," and click **Build Schedule** — expect tabs for each feasible strategy and a weekly calendar rendering the selected schedule's meeting blocks.

## Manual Verification (Phase 9)

With the stack running and all three seed scripts run (`seed_data.py`, `seed_syllabi.py`, `seed_degrees.py`):

1. `GET /api/v1/degrees` — expect 3 programs (B.S. Computer Science, B.S. Data Science, B.S. Business Analytics), each with Core/Electives/Capstone requirement groups.
2. `GET /api/v1/courses/{CS 4375's id}/prerequisites` — expect two AND'd groups: `[CS 2336]` and `[MATH 3315]`.
3. `GET /api/v1/courses/{CS 4365's id}/prerequisites` — expect one OR'd group: `[CS 3345, CS 4375]` (either satisfies it).
4. Register a user, `POST /api/v1/degree/enroll` with a `degree_program_id`, then `POST /api/v1/degree/completed-courses` with `CS 1336`'s id.
5. `GET /api/v1/degree/progress` — expect Core showing `1/4` completed with `CS 1336` listed, Electives and Capstone both showing `0` completed.
6. `GET /api/v1/degree/next-courses` — expect `CS 2336` and `CS 3377` at the top (`eligible: true`, prerequisites already satisfied), and courses like `CS 3345` further down showing `eligible: false` with `missing_prerequisites: ["CS 2336"]`.
7. Try `GET /api/v1/courses/{CS 3345's id}/eligibility` before and after marking `CS 2336` complete — expect `eligible` to flip from `false` to `true`.

## Manual Verification (Phase 10)

With the stack running:

1. `curl -D - http://localhost:8000/api/v1/health` — expect an `X-Request-ID` header on every response.
2. Call `GET /api/v1/courses/search?q=python` twice in a row (`time curl ...`) — the second call should be noticeably faster, and `docker compose exec redis redis-cli KEYS "*"` should show a `course_search:...` key.
3. Send 11+ rapid `POST /api/v1/auth/login` requests — expect `401` (bad credentials) for the first 10 and `429` (rate limited) after that.
4. Trigger a real server error (e.g. stop the `postgres` container mid-request) and confirm the response body is a clean `{"error_code": "internal_error", ...}` JSON object, never a Python traceback.
5. Run `python scripts/evaluate_rag.py` inside the backend container (after `seed_data.py` + `seed_syllabi.py`) — expect a 100% hit rate on the answerable questions and correct abstention on the unanswerable one.
6. `cd backend && ruff check .` and `pytest -q` — expect both clean (115 passing).

## Roadmap

See [`docs/architecture-proposal.md`](docs/architecture-proposal.md#g-development-roadmap) for the full 10-phase roadmap (University Data → Course/Professor UI → AI Search → Recommendation Engine → Syllabus RAG → Exam Intelligence → Schedule Optimization → Degree Planning → Production Hardening).

## Known Limitations (Phase 10)

- All course/professor/grade/syllabus data is synthetic sample data for a fictional "Northlake University" — see the Data Provenance Disclaimer below.
- The deterministic embedding fallback (used when `VOYAGE_API_KEY` is unset) is a bag-of-words hashing trick, not a trained semantic model — it supports exact/overlapping vocabulary well but won't catch paraphrases or synonyms the way a real embedding model would.
- Dense similarity search runs in application code over a per-course/professor candidate set rather than a native `pgvector` `ORDER BY … <=>` query — fine at this dataset's scale, but a scaling point worth revisiting before a large real syllabus corpus.
- The lexical half of hybrid retrieval is a simple term-overlap score, not true BM25 (see `app/retrieval/hybrid_search.py`); a production deployment would swap in Postgres full-text search or a dedicated search engine.
- Only 10 of the 20 seeded courses have a syllabus, so only those have assessment metadata; a course without one correctly shows "not available" rather than a guess.
- The rule-based assessment extractor is reliable on the seeded syllabi's consistent phrasing but is not a general-purpose parser for arbitrary real-world syllabus wording — the LLM extractor is the primary path for that, and is what a production deployment would rely on.
- `assessment_metadata` is keyed to a single syllabus per course/professor pair; if a professor's exam format changes across terms, this schema doesn't yet track multiple terms' worth of syllabi per pairing or flag disagreement between them (brief §28's "varied across semesters" case is a known gap).
- `/schedule/generate` doesn't yet accept a specific list of required courses to force-include (e.g. "make sure CS 4375 is in there") — it optimizes purely over the discovered candidate pool. Required-course pinning is a straightforward extension of the existing `required_course_ids` optimizer parameter, just not wired to the API yet.
- Schedules aren't persisted — there's no "save this schedule" yet (that's the `saved_schedules` student-profile work, later in the roadmap); each `/schedule/generate` call is stateless.
- `/schedule/generate` and `/recommendations/courses` only consider sections in the term flagged `is_active_for_planning`; a student can't yet pick a different term.
- The rule-based fallback parser (for search/recommendation/schedule queries) is a narrow set of regex rules covering the product brief's demo phrasings, not general NLU; accuracy is meaningfully better with an LLM configured.
- The Schedule Builder is the only page wired to a POST-driven backend flow so far; `/ai/search`, `/recommendations/courses`, `/rag/query`, and `/assessment/*` are still API-only, not yet surfaced anywhere in the UI.
- Professor ratings are aggregate snapshots only; individual review text and theme extraction arrive with the Review Intelligence work.
- No authentication is wired into the UI yet (backend auth API exists from Phase 1, but course/professor/schedule pages are public and stateless).
- Auth is email/password only; SSO and OAuth are future scope.
- Degree planning has no frontend UI yet — enrollment, progress, and next-course suggestions are API-only this phase.
- `/degree/next-courses` doesn't yet combine with the Recommendation Engine or Schedule Builder (e.g. "build me a schedule that also advances my degree") — it's a standalone deterministic suggestion list for now, a natural follow-on integration.
- A course can appear in more than one requirement group (e.g. a capstone course also counted as an elective) by design in the seed data; completing it satisfies both groups simultaneously, which is intentional but worth knowing when reading progress percentages.
- `degree_program_id` is a single field on `users`, so a student can only be enrolled in one degree program at a time (no double majors/minors yet).
- Caching covers two representative endpoints (course search, professor grades), not every read path — a blanket caching layer wasn't the goal; the brief calls these two out specifically as expensive/repeated.
- Rate limiting uses in-memory storage, correct for a single backend instance; a multi-instance deployment would need a shared store (Redis) so limits are enforced consistently across instances.
- The RAG evaluation script is a small fixed regression check (hit@k, abstention accuracy) against the seeded dataset, not the fuller continuous-evaluation framework described in the architecture doc (context precision/recall, faithfulness, citation correctness against a managed golden dataset). There's no equivalent recommendation-ranking evaluation harness yet (precision@k, NDCG@k) — that would need historical interaction data this synthetic dataset doesn't have.
- Mypy and pip-audit run in CI as advisory (`continue-on-error`), not blocking — current findings are third-party stub mismatches (OR-Tools' generated bindings, the Anthropic SDK's fast-moving overload signatures, slowapi's handler typing), not real bugs; every finding in first-party code was fixed.
- No HTTPS/TLS termination, secrets manager, or production deployment manifests (Kubernetes/ECS/etc.) yet — Docker Compose is a local/demo setup, not a production deployment target.
- Security headers (CSP, HSTS, X-Frame-Options) aren't set yet; would typically be added at a reverse-proxy/CDN layer in front of the app rather than in FastAPI itself.

## Data Provenance Disclaimer

All course, professor, grade, and syllabus data used during development is either sourced from official university publications or is clearly labeled synthetic/sample data generated for demonstration purposes. Synthetic data is never presented to end users as real institutional data.
