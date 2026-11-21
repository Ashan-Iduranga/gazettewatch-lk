# Capacity and cost estimate

- **Date:** 2026-11-21 (issue #4, plan item 0.4)
- **Inputs:**
  - [source-notes.md](../source-notes.md): 8,175 gazettes 2024-01 → 2026-11, 7,835 si files + 7,738 en files ≈ **15,573 PDFs**
  - [sample-corpus.md](../sample-corpus.md): pages per PDF 4.9 (base) / 8 (high)
  - text measured with PyMuPDF on the 26 corpus PDFs (250 pages), in a throwaway environment and not added to the project:
    - **mean 2,805 B/page**, median 1,630, p90 6,959
    - 1,736 characters per page
    - 2.8 % of pages over 8 KB
    - span characters: 69 % Unicode, 8 % FM legacy, 23 % Latin
- **Model:** [`capacity_model.py`](capacity_model.py) (standard library only; run `python docs/planning/capacity_model.py` to reproduce every number below). The assumptions are listed
  at the end, so the numbers can be re-run when Phase 2 gives real measurements.

## Verdict

| Limit | Result | Verdict |
|---|---|---|
| **Supabase Free DB: 500 MB** | 2024 → now ≈ **1.1 GB** (standard schema, `halfvec(768)`); ≈ 0.9 GB lean | ❌ **Does not fit.** See "Decision needed" below. |
| Supabase Free: pauses after 1 week idle, 2 projects | the daily ingest run counts as activity | ✅ ok for dev. Staging and prod can't both be free projects alongside dev. |
| Gemini embeddings: backfill | 84k chunks, ≈ 85 M tokens | ⚠️ About **$8.50 (batch) to $17** one-off on the paid tier. The free tier would take about 3 months at the unofficial ~1,000 requests/day. |
| Gemini embeddings: daily | ≈ 80 chunks/day | ✅ free tier |
| GitHub Actions (private repo) | backfill ≈ 820 min in 3 runs of ≤ 5 h; daily ≈ 7 min → ≈ 210 min/month | ✅ The backfill month uses ≈ 1,030 of 2,000 free minutes. After that it's ≈ 210/month. |
| Actions cache 10 GB | PDFs ≈ 3.7 GB | ✅ cache by SHA-256; don't store PDFs in the DB |
| OCR | 0 scans in 38 PDFs; 2 % allowance ≈ 1,500 pages | ✅ Tesseract (free, local). Gemini vision fallback only for the hard cases. |
| `/ask` (Gemini Flash, 8 chunks of context) | ≈ 9.4k input + 500 output tokens | ≈ **$0.009/question** now, ≈ **$0.018** from 1 Jan 2027 (3.8 Flash list price). 1,000 questions/month ≈ $9–18. |

## DB size detail (MB)

| case | pages | chunks | `vector(768)` | `halfvec(768)` | `halfvec(1536)` | `halfvec(3072)` | text only, no vectors |
|---|---|---|---|---|---|---|---|
| base (4.9 p/PDF) | 76,308 | 83,938 | 1,385 | 1,127 | 1,385 | 1,902 | 850 |
| high (8 p/PDF) | 124,584 | 137,042 | 2,256 | 1,835 | 2,256 | 3,099 | 1,382 |

Where the space goes (base, `halfvec(768)`):

| Part | MB |
|---|---|
| trigram GIN | 354 |
| chunk text | 250 |
| `pages.text` | 237 |
| HNSW | 154 |
| vectors | 124 |
| gazette / file rows | 9 |

**Even text with no vectors doesn't fit.** The two biggest costs are the **trigram index** (an assumption: 1.5 × the
text) and **storing the text twice** (`pages.text` + `chunks.content`).

### Scenarios that fit (`halfvec(768)`, base pages)

| Window | Gazettes | Standard schema | Lean schema* | Fits 500 MB with 20 % headroom? |
|---|---|---|---|---|
| 2024-01 → now (PRD scope) | 8,175 | 1,127 MB | 903 MB | no |
| 2025-01 → now | 5,624 | 778 MB | 624 MB | no |
| **rolling 12 months** | 2,803 | 393 MB | **316 MB** | **yes** |
| rolling 6 months | 1,401 | 201 MB | 163 MB | yes |

\*Lean = the page text is stored once (chunks hold the text; `pages` keeps only metadata and the quality score).
Growth is ≈ **35 MB/month**, so a free-tier database needs a rolling window or pruning.

## Decision needed (owner; record it in PRD v1.1, issue #12)

The PRD scope "2024 onward, si + en" doesn't fit the free database. This decision isn't mine to make, because
option B costs money and option A changes the product scope.

**Option A: rolling 12 months on Supabase Free** (recommended for v1 and the beta).
- US$0. It fits with headroom using the lean schema plus `halfvec(768)`.
- Search covers the last 12 months. Older gazettes still link out to documents.gov.lk, and the page says so.
- Needs a monthly prune job, and the eval questions have to come from the window.

**Option B: Supabase Pro (US$25/month) with the full 2024 → now range** (8 GB disk), plus the paid Gemini tier for
the backfill (≈ $9–17 once).
- About US$300/year.
- Matches the PRD. It also gives daily backups, which Free doesn't have.

**Option C:** start with A, and move to B before public launch if users ask for older gazettes. The schema is the
same either way.

Recommended regardless of option:
1. **Lean schema:** don't duplicate the text between `pages` and `chunks` (input to the ER diagram, 0.6).
2. **`halfvec(768)`** for embeddings (ADR-008).
3. **Measure the trigram index on real data** in the first Phase 2 run. It is the largest and least certain number
   here. If it's too big, put the trigram index on a normalised short field only (title / description / first
   500 characters) and rely on vector search plus an exact-number match for the body.
4. **A paid Gemini tier for the backfill** (one-off, about $9–17 with a budget cap set in Google Cloud), because the
   free tier takes months. *This needs your OK before anything is enabled (no paid tiers without asking).*
5. **Keep dev on Free with a 3–6 month window**, so the dev project stays at about 100–200 MB.

## Assumptions (edit and re-run `capacity_model.py`)

| Assumption | Value | Basis |
|---|---|---|
| PDFs (si + en) | 15,573 | full 2024+ listing |
| pages per PDF | 4.9 base / 8 high | random recon sample / deliberate corpus |
| text per page | 3,075 B | measured 2,805 + FM→Unicode growth (8 % of characters go from 1 to 3 bytes) |
| chunks per page | 1.1 | one chunk per page; the 2.8 % of pages over 8 KB are split |
| chunk prefix | 150 B | gazette no. / date / department |
| characters per token | 1.7 | assumption for Sinhala-heavy text; check with `count_tokens` in Phase 2 |
| row overhead / B-tree | 60 B + 3 × 40 B per row | Postgres rule of thumb |
| trigram GIN | 1.5 × text | **assumption, measure** |
| HNSW | (vector + 200 B neighbours) × 1.1 | m = 16 |
| TOAST compression | not counted | most pages are under 2 KB, so most text isn't compressed; this is a safety margin |
| PyMuPDF time | 0.05 s/page | rule of thumb |
| fetch rate | 1 request / 2.5 s | CLAUDE.md crawl rule |

## Sources (checked 2026-11-21)

- Supabase Free: 500 MB database per project; projects pause after 1 week of low activity; 2 active free projects.
  - [Pricing](https://supabase.com/pricing)
  - [Do free projects pause?](https://supabase.com/kb/faqs/platform/free-project-pausing)
  - [Billing](https://supabase.com/docs/guides/platform/billing-on-supabase)
- Gemini embeddings:
  - `gemini-embedding-2`: 8,192 input tokens, 128–3072 dims (768 / 1536 / 3072 recommended), truncated outputs
    normalised; $0.20 per 1M text tokens (batch $0.10)
  - `gemini-embedding-001`: 2,048 tokens, $0.15
  - The free-tier limits are only in forum posts (≈ 100 RPM / 1,000 RPD) and **aren't official**. Check the
    AI Studio quota page.
  - Links: [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings),
    [gemini-embedding-2](https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2),
    [Pricing](https://ai.google.dev/gemini-api/docs/pricing),
    [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- Gemini 3.8 Flash: $0.75 in / $3.75 out per 1M tokens until 31 Dec 2026, then $1.50 / $7.50. *(The pages
  disagree for 3.6 Flash; re-check before launch.)* [Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- GitHub Actions: 6 h per job; 10 GB cache per repo. The free private-repo allowance is shown as 2,000 minutes
  in the billing table and as $12 of included compute on the plans page.
  [Limits](https://docs.github.com/en/actions/reference/limits),
  [Billing](https://docs.github.com/en/actions/concepts/billing-and-usage),
  [Plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans)
- pgvector: `vector` = 4 × dims + 8 B, `halfvec` = 2 × dims + 8 B. HNSW supports up to 2,000 dims for `vector` and
  4,000 for `halfvec`. [Neon pgvector docs](https://neon.com/docs/extensions/pgvector)
