# PRD review and Phase 0–1 plan

- **Date:** 2026-11-19
- **Reviews:** [PRD v1](../PRD.md)
- **Status:** Draft. The open items below get closed in PRD v1.1 (issue 0.12).
- **Note:** IDs like 0.2 and 1.7 match the GitHub Issues titled `[P0] …` / `[P1] …`. After creation, the GitHub issue numbers are the reference.

---

## 1. Unclear, risky or missing in the PRD

### A. Schedule
1. **The schedule is 4 weeks with no buffer.** Phase 2 is the hardest part (crawler, legacy-font converter, quality scorer, OCR, backfill) and gets 6 days. The scorer and the converter test cases are owner-written and sit on that path.
2. **Phase 0 has 2 days for 7 outputs** (board, wireframes, ER, C4, 6 ADRs, threat model, 20 PDFs and a font list). That only works if the ADRs stay very short.
3. **"15+ beta users" can't be measured within Phase 8** (19–21 Dec). The beta has to start around Phase 6. The PRD also doesn't define how a beta user is counted when the app is anonymous by default.
4. **The 7-day ingestion streak needs the daily cron live by about 12 Dec.** The PRD should say when the streak window starts.
5. **There is no cut line.** Decide what gets dropped first if the schedule slips. Suggestion: alerts, then gazette summaries, then history.

### B. Source and legal (documents.gov.lk)
6. **robots.txt, site terms and the listing structure aren't recorded yet.** Unknowns: pagination, per-language metadata, and whether department or category comes from the listing or must be extracted from the PDF. The "filter by department" story depends on this.
7. **The corpus size isn't estimated.** "2024 onward, si + en" could mean thousands of PDFs and tens of thousands of pages. That number drives:
   - Supabase free-tier storage and HNSW index size
   - Gemini embedding quota during backfill
   - OCR cost
   - GitHub Actions run time (6 h job limit)
8. **Personal data inside gazettes is the main open policy question.** Land-acquisition, appointment and court notices contain names, addresses and sometimes NIC numbers. Three things are undecided:
   - whether gazette text sent to the LLM is masked, given that the chunks *are* the evidence
   - whether searching by a person's name is allowed
   - whether gazette pages may be indexed by search engines

   → This needs an ADR (ADR-007).
9. **Copyright and redistribution of gazette text and PDFs**, including committing sample PDFs as test fixtures. Check the IP Act position on official texts and the site terms, and record the outcome.
10. **PDPA dates and duties need checking against the current law.** Also missing from the PRD: controller identity, lawful basis, cross-border transfer (most processors are overseas), and a retention period for each store.

### C. Data model
11. **`replaced_by_no` (one text field) can't hold real gazette relations.** A gazette may amend several others, partially amend one, rescind one, or issue a corrigendum. The original may also be pre-2024 and missing from the corpus.
    → Add a `gazette_relations(from_id, to_gazette_no, kind, detected_by)` table. "Amended" ≠ "superseded".
12. **No field links the si and en versions** (user story 7). Add a group ID or a canonical join key.
13. **The `gazette_no` format and uniqueness are undefined.**
    - The same number appears as `2412/15`, `2412 / 15` and in Sinhala script.
    - The site may re-upload a corrected PDF: same number, new hash.
    - One gazette may come as several PDFs per language.
14. **No per-document retry tracking.** Each gazette needs `attempts`, `last_error` and `next_retry_at`.
15. **Embeddings aren't versioned.** Add an `embedding_model` column and fix the dimension N in an ADR (ADR-008).
16. **Gazette summaries have no home.** Undecided: storage, when they are generated, cost, and behaviour on `low_confidence` pages.
17. **Department names need normalisation** (spelling variants in two languages). Use a lookup table or a canonical code.
18. **Alerts need more columns.** Double opt-in and unsubscribe need signed, expiring tokens. `alerts_sent` needs `unique(saved_search_id, gazette_id)` so an alert can't be sent twice.
19. **Two table rules are missing:** cascade deletes from `auth.users` (so account deletion is immediate), and a mechanism for the 90-day `search_history` cleanup.

### D. Product behaviour
20. **Alert matching is undefined** (keyword, hybrid, or score threshold), and so is digest vs. one email per gazette.
21. **Ask is underspecified:**
    - single-turn or chat?
    - can a Sinhala question be answered from an English-only gazette?
    - how are Singlish (Sinhala typed in Latin letters) queries handled?
    - are `/ask` questions stored in history?
22. **The metrics need written definitions and a grader.** "Correct" and "supported" have to be defined before the 85% and ≤5% targets mean anything. The CER test needs hand-typed ground-truth pages.
23. **The refusal threshold has no calibration method.** The eval set arrives (Phase 6) after Ask is built (Phase 4).
24. **No user feedback path**, such as 👍/👎 or "report a wrong answer".
25. **The disclaimer has no wording or placement**, and nothing says how legal-advice questions are handled.

### E. Infrastructure and cost
26. **A sleeping free-tier API host breaks "first token < 5 s p95".** Plan a keep-alive or a paid instance, or define p95 as measured warm.
27. **Supabase free-tier limits:**
    - projects pause after inactivity
    - only 2 free projects, so staging has nowhere obvious to go
    - the default auth email rate limit is very low, so custom SMTP is needed for magic links
28. **Client IP behind proxies.** If forwarded headers aren't trusted correctly, the rate limiter sees one shared proxy IP for every user.
29. **The Turnstile flow for a streamed `/ask` is undefined.** It should be one token per question, verified before streaming starts.
30. **Ingest on GitHub Actions** needs Tesseract `sin` installed and a resumable backfill (6 h limit). It also needs a lock against overlapping runs and has to tolerate delayed cron runs.
31. **No LLM spend cap or budget alert.**
32. **No decision on whether the web app reads Supabase directly (anon key + RLS) or only through the API.**

---

## 2. Edge cases and missing NFRs

### Edge cases

**Ingestion**
- **Listing and network failures:**
  - the listing HTML or pagination changes; the crawler should fail loudly, not ingest 0 silently
  - the site is down or slow, TLS errors, 403/404, or a truncated download
- **Re-uploads and late listings:**
  - a corrected re-upload (same number, new hash) must not create a duplicate
  - a gazette listed late with an older date gets missed by a `--since` window; use an overlap window or diff the listing
- **Problem PDFs:** scanned, encrypted, corrupt or malicious ones (cap size and pages), and very large ones (hundreds of pages).
- **Hard layouts and fonts:**
  - rotated tables and multi-column pages
  - several languages in one PDF
  - legacy and Unicode fonts mixed on one page
  - subset-prefixed font names (`ABCDEF+FMAbhaya`)
- **Quota and errors mid-backfill:** an LLM quota or 5xx partway through must leave the run resumable, with each gazette written in one transaction.
- **Time zones:** cron runs in UTC; gazette dates are Asia/Colombo.

**Search and Ask input**
- **Unicode:** different Sinhala keyboards produce non-NFC text or ZWJ/ZWNJ variants, and text pasted from PDFs carries zero-width characters.
- **Spelling variants:** Singlish, English place-name variants, and a gazette number typed with or without spaces or "No.".
- **Filters and paging:** `from > to`, future dates, a page past the end, a department name sent in the other language.
- **Query text:** empty, whitespace-only or very long queries, and `%`, `_`, `\` in trigram or LIKE paths.

**Ask**
- **Prompt injection** inside gazette text.
- **Status conflicts:** a cancelled or amended gazette is cited, or the original and its amendment are both retrieved.
- **Relative time:** "latest" or "this year" needs today's date and `published_on` in the context.
- **Numbers and tables** (amounts, lot numbers, extents): quote the figure exactly from the cited chunk.
- **Bad citations or language:** the model cites a chunk that wasn't retrieved, or answers in the wrong language. Validate after generation.
- **User PII:** the user's own NIC or phone number in the question must be masked before the LLM and the logs.
- **Disconnects:** if the client leaves mid-stream, cancel the upstream LLM call.

**Accounts and alerts**
- **Deletion timing:** the account is deleted while the alert job is running.
- **Unsubscribe and email:** the unsubscribe link is reused, expired or forged; the email bounces; the email address changes.
- **Sign-in links:** a magic link opened on another device; an expired opt-in link.
- **History and limits:** history turned off (are existing items deleted?), an export with no data, a limit on saved searches.
- **Status changes:** a saved gazette is later cancelled.

### NFRs not yet in the PRD
- **Availability and recovery:** an uptime target, RPO/RTO, and a backup/restore plan.
- **Retention:** one table for every store (DB, logs, error tracking, LLM traces, email logs, cached PDFs), plus what "delete account" can't reach (backups, third-party logs).
- **Cost:** maximum cost per `/ask`, a monthly ceiling and budget alerts. Search must keep working when the LLM is unavailable.
- **Limits:** on question length, saved searches and page size, plus timeouts for API and LLM calls.
- **Web performance on mobile networks:**
  - a page-weight budget
  - Noto Sans Sinhala subsetting and `font-display`
  - Core Web Vitals targets
- **i18n:** Sinhala date and number formats, and correct `lang` attributes.
- **Accessibility beyond "basics":** keyboard navigation, focus states, screen-reader-friendly citation chips, reduced motion, contrast.
- **Security:**
  - CSP, HSTS and frame-ancestors headers
  - the crawler fetches only from documents.gov.lk (SSRF guard)
  - PDF size and time limits
  - secret scanning and dependency audit in CI
- **LLM observability:** the prompt version and model ID are stored with each trace.
- **Maintainability:** a minimum-test rule per module, generated DB types, and a forward-only numbered migration policy.
- **SEO and indexing policy** for gazette pages (tied to item 8).
- **Repo licence** and attribution to documents.gov.lk on every gazette page.
- **Crawler contact:** use a project contact address (not a personal one) in the crawler User-Agent.

---

## 3. Phase 0 and Phase 1 issues

Labels:
- phase: `phase-0`, `phase-1`
- area: `docs`, `infra`, `db`, `web`, `api`, `ingest`, `security`, `privacy`, `design`
- other: `priority:high` (⭐), `owner:ashan` (the owner writes it), `stretch`

### Phase 0: Plan & design (24–25 Nov)

**0.1 ⭐ Repo hygiene and project board**
- [x] Private notes stay git-ignored
- [ ] GitHub Project board with columns Backlog / Ready / In progress / Review / Done; labels created
- [ ] Issue templates (feature, bug) and a PR template with the "lint + typecheck + tests run" checklist
- [ ] Branch protection on `main`: PR required, CI must pass (once CI exists)

**0.2 ⭐ Source reconnaissance: documents.gov.lk**
- [ ] `docs/source-notes.md` records:
  - robots.txt rules
  - site terms (with the date checked)
  - listing URL and pagination
  - available fields
  - PDF URL pattern
- [ ] Gazette number format(s) observed; canonical format decided
- [ ] Volume estimate: Extraordinary gazettes per month × languages × average pages, 2024 to now
- [ ] Notes on re-uploads, multi-part gazettes and multi-language PDFs, with examples
- [ ] Recon kept to at most 1 request every 2 s, with a descriptive User-Agent

**0.3 ⭐ Sample corpus and font inventory**
- [ ] 20 PDFs that cover:
  - Unicode Sinhala
  - legacy-font Sinhala (≥ 2 fonts)
  - scanned/image-only
  - English
  - table-heavy
  - very large
  - an amendment or rescinding gazette
  - an si+en pair
- [ ] `docs/sample-corpus.md`: source URL, SHA-256, language and reason for each PDF
- [ ] Font list: each font name (prefix-stripped) classed as Unicode / known legacy / unknown
- [ ] Decision on whether PDFs are committed as fixtures or only referenced by URL + hash

**0.4 Capacity and cost estimate**
- [ ] Estimated rows (gazettes, pages, chunks) and DB size, including vectors and HNSW, against the free-tier limit
- [ ] Backfill embedding calls and time against free-tier quotas; estimated OCR pages and cost
- [ ] GitHub Actions minutes per daily run and for the backfill
- [ ] Result says "fits free tier" or names the constraint and its mitigation

**0.5 ADRs 001–008** (one page each; the owner decides)
- [ ] ADR-001 to ADR-006 as planned in `docs/adr/0000-template.md`
- [ ] ADR-007 Personal data in gazette text: LLM masking, name search, indexing, retention
- [ ] ADR-008 Embedding model and dimension: model ID, N, `embedding_model` column, re-embed strategy
- [ ] ADRs linked from README

**0.6 ER diagram and data-model update**
- [ ] Mermaid ER diagram in `docs/architecture/data-model.md` with the §1C additions
- [ ] RLS intent per table (select / insert / update / delete)
- [ ] PRD §4 updated to match

**0.7 C4 context and container diagrams**
- [ ] Mermaid C4 context diagram: users, documents.gov.lk, external services
- [ ] Container diagram showing web / api / ingest / DB and where each secret lives
- [ ] Decision on whether web reads Supabase directly or only through the API

**0.8 Threat model**
- [ ] `docs/security/threat-model.md`: STRIDE per container, plus the OWASP LLM Top 10 mapped to `/ask`
- [ ] Covers:
  - prompt injection via gazette text
  - malicious PDFs
  - `/ask` cost abuse
  - forwarded-header spoofing
  - token leakage
  - RLS bypass
- [ ] Each threat has a mitigation and a linked issue

**0.9 Privacy notes**
- [ ] `docs/privacy/data-inventory.md`: for each personal-data field, its purpose, lawful basis, store, retention and processor
- [ ] Processor list with country, plus a cross-border note
- [ ] PDPA dates and duties checked, with sources cited
- [ ] Draft of what "delete account" removes and what it can't

**0.10 Wireframes (si + en, 360 px and desktop)**
- [ ] Screens: search, results and filters, gazette page, Ask with citations, not-found/refusal, settings, saved searches, export/delete
- [ ] Empty, loading, error and rate-limited states
- [ ] Disclaimer placement shown
- [ ] Design references and style guide used are named

**0.11 Evaluation plan** (`owner:ashan` writes ≥ 20 of the 100 questions)
- [ ] Definitions of "correct", "supported" and "correct refusal"; grading method
- [ ] Question template: question, language, expected gazette/page, expected answer, type
- [ ] CER method: page selection, ground-truth typing, tool
- [ ] Mix includes ≥ 10 should-refuse questions and ≥ 10 Singlish questions

**0.12 PRD v1.1: close the open questions**
- [ ] Every item in §1 marked decided (with a link), deferred, or accepted risk
- [ ] Cut line agreed
- [ ] Beta start date and the definition of a beta user

### Phase 1: Foundation (26–28 Nov)

**1.1 ⭐ Dependency register**
- [ ] `docs/dependencies.md`: every planned dependency with weekly downloads, repo URL, licence, reason and owner approval
- [ ] Nothing is installed before its row is approved

**1.2 ⭐ Monorepo skeleton**
- [ ] `apps/web`, `apps/api`, `apps/ingest` and `supabase/migrations` created; README has setup steps for Windows/PowerShell
- [ ] `.editorconfig` and `.gitattributes` (LF normalisation)
- [ ] `.env.example` updated; no real values

**1.3 apps/web scaffold**
- [ ] Next.js App Router + TypeScript, Tailwind and shadcn/ui
- [ ] next-intl with `/si` and `/en`, a language switcher and a `lang` attribute per locale
- [ ] Noto Sans Sinhala via `next/font`, subset, no layout shift
- [ ] Placeholder home page in both languages works at 360 px
- [ ] lint, typecheck and Vitest smoke test pass
- [ ] No server secrets in any `NEXT_PUBLIC_*` variable

**1.4 apps/api scaffold**
- [ ] FastAPI + Pydantic v2 settings; the app fails fast on missing env vars
- [ ] `GET /health` returns `{status:"ok"}`
- [ ] CORS allows only `WEB_ORIGIN` (tested)
- [ ] Generic error handler; request bodies never logged
- [ ] ruff and pytest pass; Dockerfile builds on the host

**1.5 apps/ingest scaffold**
- [ ] `python -m ingest.run --since YYYY-MM-DD --dry-run` exits 0 without network calls
- [ ] Invalid `--since` gives a clear error and a non-zero exit (tested)
- [ ] User-Agent and the 2 s throttle are configurable; the throttle is tested
- [ ] ruff and pytest pass

**1.6 ⭐ Supabase dev project and migration workflow**
- [ ] Cloud dev project; keys only in local `.env` and host dashboards
- [ ] Migration workflow without Docker documented; numbered migrations
- [ ] `vector` and `pg_trgm` enabled in migration 0001
- [ ] Custom SMTP noted as a Phase 5 prerequisite

**1.7 Migrations: public tables**
- [ ] `gazettes`, `pages`, `chunks`, `ingest_runs` plus the 0.6 additions
- [ ] Unique, check and NOT NULL constraints, and FKs with cascade
- [ ] HNSW, trigram GIN and B-tree indexes
- [ ] RLS on every table; writes only by the service role
- [ ] Applies cleanly to an empty DB

**1.8 Migrations: user tables and RLS**
- [ ] `profiles` (created by trigger; history off by default), `saved_searches`, `search_history`, `alerts_sent` (+ tokens)
- [ ] RLS: `owner_id = auth.uid()` for every operation; users can't write `alerts_sent`
- [ ] Cascade on `auth.users` delete
- [ ] Length checks on text columns

**1.9 ⭐ RLS and permission tests**
- [ ] anon can't read user tables or write public tables
- [ ] User A can't read, update or delete user B's rows
- [ ] The user can CRUD only their own rows
- [ ] A catalog test fails if any `public` table lacks RLS
- [ ] Runs in CI against a test project or schema, never prod

**1.10 ⭐ CI (GitHub Actions)**
- [ ] On PR: web (lint, typecheck, test), api (ruff, pytest), ingest (ruff, pytest), with path filters and caching
- [ ] Secret scanning and dependency audit
- [ ] Secrets only from Actions secrets; least-privilege `permissions:`
- [ ] README badge; `main` requires green CI

**1.11 Staging deploy**
- [ ] Web on Vercel and API on Render, with env vars set in the dashboards
- [ ] Staging works in si and en; `/health` is reachable; CORS blocks other origins
- [ ] The Supabase project used for staging is documented
- [ ] Uptime monitor on `/health`; cold-start time measured

**1.12 (stretch) JWT verification for `/me/*`**
- [ ] A dependency verifies the Supabase JWT (signature, expiry, audience); the user ID comes from the token only
- [ ] Tests cover no token, bad signature, expired token and valid token; error bodies are generic
