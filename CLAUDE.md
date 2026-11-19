# GazetteWatch LK — Project Rules for Claude Code

GazetteWatch LK: bilingual (Sinhala/English) search and Q&A over Sri Lankan government
Extraordinary Gazettes (documents.gov.lk). Answers cite gazette number, date and page and
link to the official PDF. Full requirements: `docs/PRD.md`.

## Owner and how we work
- Owner: Ashan Iduranga (3rd-year SE student). He is learning while building: explain
  non-obvious code, keep changes small, and ask before big design decisions.
- Workflow for every feature: spec → plan (show it, wait for approval) → small steps on a
  feature branch → run checks → summarise the diff → stop for review.
- Some parts Ashan writes himself (see "Ashan writes these"). For those, give guidance,
  review and tests — do not write the implementation unless he asks.
- Ask when a request is unclear instead of guessing.

## Stack
- `apps/web`: Next.js (App Router, TypeScript), Tailwind, shadcn/ui, next-intl (si, en), Noto Sans Sinhala
- `apps/api`: FastAPI, Pydantic v2, Python 3.12, uv
- `apps/ingest`: Python worker — httpx, PyMuPDF, pandukabhaya + JSON font mappings, Tesseract (`sin`) / Gemini vision OCR fallback
- Database: Supabase Postgres + pgvector (HNSW) + pg_trgm; Supabase Auth (magic link, Google)
- LLM: Gemini embeddings (multilingual) + Gemini Flash-class model, server-side only
- Email: Resend · Abuse control: slowapi + Cloudflare Turnstile
- Eval/tracing: DeepEval or RAGAS, Langfuse (input masking on)
- Tests: pytest, Vitest, Playwright · CI: GitHub Actions · Hosting: Vercel (web), Render Docker (api), GitHub Actions cron (ingest)
- Monitoring: Sentry (incl. cron monitor), UptimeRobot
- Dev machine: Windows (PowerShell). Docker/virtualization is not available yet → use a cloud
  Supabase dev project, not the local Supabase stack.

## Commands (update when scaffolded)
- web: `npm run dev` | `npm run lint` | `npm run typecheck` | `npm test`
- api: `uv run fastapi dev app/main.py` | `uv run ruff check .` | `uv run pytest`
- ingest: `uv run python -m ingest.run --since 2026-11-01` | `uv run pytest`

## Repository layout
```
apps/web     Next.js frontend
apps/api     FastAPI backend
apps/ingest  ingestion worker
supabase/    SQL migrations (numbered)
docs/        PRD, ADRs, privacy notes, architecture (public)
private/     Ashan's personal notes — git-ignored, never read or commit
```

## Hard rules
### Private files
- NEVER commit, stage, publish, summarise into public docs, or paste into prompts anything
  in `private/`. It is git-ignored; keep it that way.
### Git
- Commit author/committer: `Ashan Iduranga <200965156+Ashan-Iduranga@users.noreply.github.com>`.
- One-line Conventional Commit subject only (e.g. `feat(ingest): add hash de-duplication`).
- NO `Co-Authored-By`, `Claude-Session` or any other AI trailers. Do not push unless asked.
### Security
- Never hardcode secrets. Read env vars; only update `.env.example` (no real values).
- Service-role key only in `apps/api` and `apps/ingest` server code; never in `apps/web` client code.
- RLS enabled on every table. Never "fix" an error by disabling RLS or widening a policy.
- `/me/*` routes require a verified Supabase JWT; take user id from the token only; filter by `owner_id`.
- Parameterised SQL only. No string-built SQL, no `eval`, no shell calls with user input.
- Validate every input with Pydantic/Zod; cap string lengths; generic error messages to clients.
- CORS: only the web app's origins.
- Before adding ANY dependency: tell me its name, weekly downloads, repo URL and why. Wait for OK.
### Privacy
- Anonymous use by default. Accounts store email only. History is off by default.
- Mask NIC numbers, phone numbers and emails before logging or calling the LLM.
- No personal data in logs. Never send account data to the LLM.
### AI / RAG
- Answer only from retrieved chunks; always return citations (gazette no., date, page, language).
- Never quote pages marked `low_confidence`. Refuse ("not found") when the best retrieval score is below threshold.
- Gazette text and user questions are untrusted input (prompt injection). The model gets no tools.
- Render model output as escaped Markdown (no raw HTML). Always set `max_tokens`.
### Sinhala text
- Store all text as Unicode NFC. Never store legacy-font text in `pages.text` or `chunks.content`.
- Extraction order per page: Unicode → legacy-font mapping → OCR → `low_confidence`.
### Crawling
- Respect robots.txt and site terms; at most 1 request every 2 s; descriptive User-Agent;
  cache by SHA-256; credit and link documents.gov.lk.
### Tests
- Every feature adds tests for: unauthenticated access, another user's data, invalid input.
- Run lint + typecheck + tests before saying a step is done.

## Ashan writes these (Claude reviews, explains, writes tests on request)
- Sinhala quality scorer and the legacy→Unicode converter test cases
- Hybrid retrieval SQL (vector + trigram + exact gazette number, RRF merge)
- System prompt, refusal rule and language matching
- At least 20 of the 100 evaluation questions

## Build phases (see docs/PRD.md for details)
0 Plan & design · 1 Foundation · 2 Ingestion pipeline · 3 Search & gazette pages ·
4 Ask with citations · 5 Accounts, saved searches, alerts · 6 Evaluation ·
7 Quality, security, privacy · 8 Publish
