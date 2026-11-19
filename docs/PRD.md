# GazetteWatch LK — Product Requirements (v1)

## 1. Product brief
- **Problem:** hundreds of Extraordinary Gazettes are published every year on documents.gov.lk in one long list. Many Sinhala PDFs use legacy (non-Unicode) fonts, so they can't be searched or copied.
- **Users:** citizens and landowners, small businesses, journalists, law and public-administration students.
- **Goal:** find the right gazette in seconds and get a plain-language answer in Sinhala or English, always linked to the official PDF.
- **Non-goals (v1):** not legal advice; no Tamil; no ordinary weekly gazettes; no mobile app; no payments.
- **Corpus v1:** Extraordinary Gazettes from 2024 onward, Sinhala and English versions.

### Success metrics
- ≥ 85% correct answers on a 100-question test set (50 Sinhala, 50 English)
- ≤ 5% answers not supported by the cited page
- Sinhala character error rate (CER) ≤ 5% on 30 hand-checked pages
- 7 consecutive days of successful daily ingestion
- 15+ beta users

### MoSCoW
| Priority | Features |
|---|---|
| Must | Search with filters; ask in Sinhala/English with citations + official PDF links; legacy font conversion + OCR fallback; daily ingestion; anonymous use; disclaimer; cancelled/amended warnings |
| Should | Optional account: saved searches, email alerts, history (off by default); export/delete my data; gazette pages with plain-language summaries |
| Could | Tamil; fine-tuned Tesseract; Telegram/WhatsApp alerts; weekly gazettes; re-ranking |
| Won't (now) | Legal advice, paid plans, mobile app |

## 2. User stories
1. **Search** — When I search "Gampaha land acquisition", I see matching gazettes (number, date, title, language) within 2 s, filterable by date and department.
2. **Ask in my language** — When I ask in Sinhala, the answer is in Sinhala with citation chips (gazette no., date, page, language) opening the official PDF; the English version is linked if it exists.
3. **Honest when unsure** — If nothing relevant (or only low-confidence pages) is found, I see "Not found in the gazettes we have".
4. **Status warning** — A cited cancelled/amended gazette shows a warning linking to the newer one.
5. **Saved search + alerts** — Given I saved "Homagama" with alerts on (double opt-in), when a matching gazette is ingested, I get one email within 24 h with an unsubscribe link.
6. **Privacy controls** — History is off by default; I can turn it on, delete items, export my data (JSON) and delete my account (all data removed immediately).
7. **Daily ingestion (system)** — New gazettes are fetched, converted, indexed and linked to their other-language versions daily; failures are logged and retried; no duplicates.

## 3. Non-functional requirements
| Area | Requirement |
|---|---|
| Accuracy | ≥ 85% correct; CER ≤ 5%; every answer cites a source |
| Language | Sinhala + English UI and answers; stored text is Unicode NFC |
| Performance | Search < 2 s; first answer token < 5 s (p95) |
| Privacy | PDPA No. 9 of 2022 (core duties from 1 Jan 2027): policy, purpose, retention, breach plan, user rights |
| Security | OWASP Top 10:2025 + OWASP LLM Top 10 (2026); RLS on every table |
| Cost | Free tiers to build; Gemini paid tier before public launch; per-IP and per-user limits |
| Crawling | robots.txt + terms; ≤ 1 request / 2 s; cache by hash; credit source |
| Accessibility | WCAG 2.2 AA basics; Noto Sans Sinhala; works at 360 px |

## 4. Data model
**Public (read-only via API; worker writes with service key)**
- `gazettes` (id, gazette_no, language si/en/ta, published_on, title, department, category, source_url, pdf_sha256, status active/cancelled/amended, replaced_by_no, page_count, ingest_status) — unique (gazette_no, language)
- `pages` (id, gazette_id, page_no, text, method unicode/mapped/ocr, quality_score, low_confidence)
- `chunks` (id, gazette_id, page_no, language, content with metadata prefix, embedding vector(N)) — HNSW + trigram indexes
- `ingest_runs` (id, started_at, finished_at, new_count, failed_count, notes)

**User (RLS: owner_id = auth.uid())**
- `profiles` (id, preferred_language, history_enabled default false)
- `saved_searches` (id, owner_id, query, filters jsonb, alert_enabled, alert_confirmed, last_notified_at)
- `search_history` (id, owner_id, query, created_at) — only when history on; 90-day cleanup
- `alerts_sent` (id, saved_search_id, gazette_id, sent_at)

## 5. API
| Method | Path | Purpose |
|---|---|---|
| GET | /health | Uptime |
| GET | /gazettes | Search (q, from, to, department, language, page) |
| GET | /gazettes/{id} | One gazette + summary + versions + status |
| POST | /ask | Streamed answer + citations (rate-limited, Turnstile) |
| GET/POST/DELETE | /me/saved-searches | Saved searches and alerts |
| GET/DELETE | /me/history | History |
| PATCH | /me/settings | Language, history on/off |
| GET | /me/export | Export my data |
| DELETE | /me | Delete account and data |

Ingestion is a scheduled script, not an API route.

## 6. Sinhala pipeline
1. Read listing → download politely → SHA-256 → skip known files
2. PyMuPDF: text spans + font names per page
3. Method: Unicode/English keep → legacy font → mapping (pandukabhaya / own JSON) → no text → OCR
4. NFC normalisation; ZWJ handling
5. Quality score (Sinhala-block ratio, word-list hit rate, invalid sequences) → OCR retry → `low_confidence`
6. Tables as row groups
7. Chunk per page with gazette no./date/department prefix
8. Embed (multilingual) + trigram index
9. Link language versions; read status (cancelled/amended)

## 7. Build phases (24 Nov – 21 Dec 2026)
| Phase | Dates | Output |
|---|---|---|
| 0 Plan & design | 24–25 Nov | Issues board, wireframes, ER + C4 diagrams, ADR-001…006, threat model, 20 sample PDFs + font list |
| 1 Foundation | 26–28 Nov | Monorepo, Supabase dev project, migrations, RLS, CI, staging deploy |
| 2 Ingestion | 29 Nov – 4 Dec | Crawler, converter, scorer, OCR fallback, chunk/embed, backfill, daily cron |
| 3 Search & pages | 5–7 Dec | Hybrid search API, gazette pages, si/en UI |
| 4 Ask | 8–11 Dec | Retrieval, prompt, streaming, citations, refusal, limits, PII scrubber |
| 5 Accounts | 12–14 Dec | Auth, settings, history, saved searches, alerts, export/delete |
| 6 Evaluation | 15–16 Dec | CER test, 100-question set, Langfuse, tuning |
| 7 Quality & security | 17–18 Dec | Tests, scanners, ZAP, security/privacy review |
| 8 Publish | 19–21 Dec | Legal pages, paid Gemini, domain, beta → public, README, demo |
