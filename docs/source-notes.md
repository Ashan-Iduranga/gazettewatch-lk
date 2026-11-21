# Source notes: documents.gov.lk (Extraordinary Gazettes)

- **Checked:** 2026-11-21 (issue #2, plan item 0.2)
- **Method:** manual recon with a browser plus a small throttled script (≥ 2.5 s between requests, User-Agent
  `GazetteWatchLK-recon/0.1 (non-commercial research crawler; max 1 req/2s)`). About 40 requests in total:
  pages, 5 listing calls and 12 sample PDFs.
- **Re-check before Phase 2.** The site was rebuilt recently (its news item says "new website"), and several
  details below are tied to its current build.

---

## 1. robots.txt and site terms

| Item | Finding |
|---|---|
| `/robots.txt` | **None.** It returns the site's HTML 404 page, so there are no crawl rules. |
| `/sitemap.xml` | None (404). |
| Terms / privacy / copyright pages | **None found.** `/web/terms`, `/web/privacy_policy` and `/web/copyright` return the generic empty CMS page. The footer says only "© 2025 All Right Reserved. Solution by LankaCom". |
| `<meta name="robots">` | `noindex` on the 404 page only. |
| Contact | gpinfo@documents.gov.lk, 0112 694 733-36 (Department of Government Printing). |

**What this means for us**
- No robots.txt does **not** mean anything goes. We keep the CLAUDE.md crawl rules: at most 1 request every 2 s,
  a descriptive User-Agent, caching by SHA-256, and credit plus a link on every gazette page.
- No published terms, so the copyright and redistribution question (PRD review item 9) stays open. Options:
  - email gpinfo@ to describe the project and ask for no-objection (recommended; the owner decides)
  - record the IP Act position on official texts in ADR-007 / the privacy notes
- Until that's settled, **reference sample PDFs by URL + hash and don't commit them** (0.3).

## 2. How the listing works

The site is a Next.js app. The "Extra Gazettes" page is `https://documents.gov.lk/web/extra_gazettes`
(the site's own label is "Extra Gazzetes"). The table is filled by a **Next.js Server Action**:

```
POST https://documents.gov.lk/web/extra_gazettes
Headers:  next-action: <build-specific action id>
          accept: text/x-component
          content-type: text/plain;charset=UTF-8
Body:     [{"apiEndpoint":"http://gvp-api:4500/website-data/extra-gazette/get-all",
            "page":1,"limit":10,"q":"","search":"",
            "forwarded":{"dateFrom":"2024-01-01","dateTo":"2024-12-31"}}]
```

The response is in React Server Components format. Line `1:` holds plain JSON:

```json
{"data":[ ...rows... ],
 "pagination":{"total":2551,"page":1,"limit":10,"totalPages":256}}
```

- **Pagination:** `page` + `limit`. The UI uses `limit=10`, and the server also accepts `limit=100`. Ordering is
  by `date` descending; rows with the same date are **not** ordered by number.
- **Filters:** `forwarded.dateFrom` / `dateTo` (ISO dates, inclusive). The UI's Year / Month / Day selects just
  set these. There is also a keyword box (`q`/`search`); it's not needed for crawling.
- **No language filter:** each row carries all of its language files.

### Risks in this interface
1. **The action id is build-specific.** `next-action` changes whenever the site is redeployed. The crawler
   should either read it from the page's JS chunk at the start of each run, or fail loudly with a clear error.
   It must never silently ingest 0 rows (PRD review §2).
2. **The body names an internal backend URL** (`apiEndpoint`). We send exactly the value the site's own page
   sends, hard-coded and never changed. We must not experiment with this field; doing so would be probing their
   backend. *(Possible issue on their side: the owner could report it to gpinfo@ / CERT|CC as a courtesy. Not
   tested.)*
3. **This is not a public, documented API.** It can change without notice. Keep the parser small and well
   tested, and add a Sentry alert for "listing returned 0 rows / schema changed".
4. A plain HTML fallback doesn't exist: the first HTML response has no rows.

## 3. Fields in each row

| Field | Example | Notes |
|---|---|---|
| `id` | `05f3cc95-…` (UUID) | Stable site id. Store it as `source_id`. |
| `gazetteNo` | `2515` (int) | |
| `gazetteSubNo` | `1` (int) | |
| `gazetteNoText` | `"2515/01"` | Always `{no}/{sub zero-padded to 2}` in the sample. One row had a 3-digit sub (`NNNN/NNN`). |
| `date` | `"2026-11-16T00:00:00.000Z"` | The gazette date stored as UTC midnight. Treat it as a **date only** (Asia/Colombo). |
| `descriptionSinhala/Tamil/English` | `"Sri Lanka Customs - Rates of Exchange"` | **The same English text in all three fields** in 100/100 sampled rows. In 6/100 it's just the gazette number. |
| `keywordsSinhala/Tamil/English` | `null` | Empty in 100/100. |
| `updatedAt` | `"2026-11-18T07:25:33.890Z"` | Usually 1–6 days **after** `date`, because files are uploaded later. |
| `contents[]` | `{language, originalFileName, uploadedFile}` | 0–3 entries; `language` ∈ `SINHALA`, `TAMIL`, `ENGLISH`. |

**Department / category:** there is no structured field. The description often starts with the issuer
(`"Ministry of Agriculture, Livestock, Land and Irrigation - Land Acquisitions under sect .38 (a)"`,
`"Election Commission"`), but not always. The PRD's "filter by department" needs:
- parsing the description where it has a "Issuer - Subject" shape, **plus**
- extraction from the PDF's first page as a fallback, **plus**
- a normalisation table (PRD review item 17).

## 4. PDF URLs

```
https://documents.gov.lk/api/content-file-proxy?file=/<uploadedFile, URL-encoded>
e.g. …?file=/extra-gazette-content/G%2048538%20(S)_1794986718.pdf
```

- **Content-Type:** `application/pdf`. Sample sizes were 130–572 KB, about 250 KB on average.
- **`uploadedFile`** is `extra-gazette-content/<original name>_<unix upload time>.pdf`. A re-upload gets a new
  timestamp and so a **new URL**. Detect changes by `(source_id, language)` + `uploadedFile` + SHA-256, not by URL alone.
- **`originalFileName`** is the printer's internal job name. These are internal ids, **not** gazette numbers:
  - `G 48538 (S).pdf` and `PG 8150 (E).pdf` are the most common shapes
  - names may carry a language suffix `(S)`/`(E)`/`(T)` or a bare `S`
  - some carry extra tags: `(C)`, `[Sec. 38]`, `[IV - B] [Kataragama PS]`

  `G`/`PG` and `(C)` are not yet understood. Don't parse these names for meaning; use the row fields.
- **The si/en pairing problem (PRD review item 12) is solved by the source:** each language file hangs off the
  same row. Join key = `source_id`.

## 5. Gazette number formats

- The listing gives clean integers: `gazetteNo` + `gazetteSubNo`.
  - **Canonical form:** store both integers. Unique key: `(gazette_no, gazette_sub_no)`.
  - Display: `{no}/{sub:02d}` (no extra padding when the sub-number has 3 digits).
- No duplicate numbers in the 100-row sample. A **uniqueness check over the full 2024+ listing** is still to do;
  it's cheap (≈ 82 listing calls) and belongs in the first ingest dry-run.
- **User and PDF input will vary.** Inside PDFs and queries, expect forms like `2515/01`, `2515 / 1`, `No. 2515/01`
  and the Sinhala `අංක 2515/01`. Normalise with one regex `(\d{4})\s*/\s*(\d{1,3})` → `(no, sub)`.
- Sub-numbers within one main number (e.g. 2514/32 … 2514/47) cover the same week.

## 6. Languages and fonts (first look, 12 PDFs)

**Language coverage** (100 rows, Oct–Nov 2026):

| Languages | Rows |
|---|---|
| si + ta + en | 60 |
| si + en | 27 |
| en only | 7 |
| si only | 2 |
| si + ta | 1 |
| **no files** | 3 |

→ Sinhala in 90 %, English in 94 %, and both si + en in about 87 %.

**Fonts** (prefix-stripped `/BaseFont` names):
- **Unicode Sinhala:** `IskoolaPota`, `IskoolaPota-Bold` in every Sinhala PDF, and also inside English PDFs for headers.
- **Legacy (FM) Sinhala:** `FMAbhayax`, `FMAbabldBold` in most InDesign-made PDFs, **mixed with Iskoola Pota in
  the same file** (and `FMAbabldBold` even shows up in some English PDFs). So the font has to be decided
  **per text span**, not per page. This matters for the extraction order in CLAUDE.md.
- **Latin and other:** Times New Roman, Calibri, Minion Pro, Courier New. One Tamil-capable font
  (`Latha`, `Arial Unicode MS`) appears in a Publisher-made PDF.
- **Producers:** Adobe InDesign 19.4 (most), Acrobat Distiller via PScript5 (some), Microsoft Publisher 2010 (one).
  Each file has 1–2 images (probably the emblem/header). No image-only scans in this small sample, but older
  years need checking in 0.3.

## 7. Volume estimate (2024-01-01 → 2026-11-16)

| Year | Extraordinary gazettes (listing `total`) |
|---|---|
| 2024 | 2,551 |
| 2025 | 2,973 |
| 2026 (to 16 Nov) | 2,651 |
| **Total** | **≈ 8,175** |
| All years on the site (1975→) | 39,450 |

That's about 210–250 gazettes a month (Jan 2024: 207, Jun 2024: 153), or **about 8 a day**.

| Quantity | Estimate | Basis |
|---|---|---|
| si + en PDFs | **≈ 15,000** | 8,175 × 1.84 files (si 0.90 + en 0.94) |
| Pages | **≈ 45k–75k** | 12-PDF sample: median 2, mean 4.9 (one 37-page outlier) |
| Download size | **≈ 3.7 GB** | ≈ 250 KB per PDF |
| Backfill time at 1 req / 2.5 s | **≈ 10.5 h** of PDF fetching, plus ≈ 82 listing calls | more than the 6 h GitHub Actions job limit |
| Daily new | ≈ 8 gazettes, ≈ 15 si+en PDFs, ≈ 1 min of fetching | |

**What this feeds into**
- **0.4 capacity:**
  - 45k–75k pages → roughly 70k–120k chunks
  - at 768 dims × 4 bytes ≈ 3 KB per vector, plus the HNSW index, plus text, this is likely to **pass the
    Supabase free-tier 500 MB**
  - options to compare in 0.4: a smaller dimension, `halfvec`, a narrower backfill window, or a paid tier
- **Backfill:** must be resumable and split across several runs or days. Don't keep PDFs in the DB. Keep only the
  hash and the source URL, and cache files in the runner or Actions cache.
- **The sample is small.** Refine the page mean in 0.3 with the 20-PDF corpus, and with `pages` counted for a
  random 100 PDFs during the first dry-run.

## 8. Incremental sync and re-uploads

- **Late uploads are normal.** `updatedAt` trails `date` by up to 6 days, and a row can show up before all its
  language files are uploaded.
  - So a `--since` date window alone misses files. The daily run should re-list the **last 14 days** and diff
    each row's `contents[]` against what we have.
  - Rows with 0 files: store the row and retry the files later (per-document `attempts` / `next_retry_at`,
    PRD review item 14).
- **Re-uploads:** a corrected file gets a new `uploadedFile` timestamp under the same `source_id` + `language`.
  Keep the newest and record the old hash.
- **Multi-part gazettes:** in the sample each language had at most one file per row. Watch for more than one in
  the full listing; the parser should accept a list anyway.

## 9. Open questions (carry to 0.3 / 0.4 / 0.12)

- [ ] Full 2024+ listing pass: unique `(no, sub)`? any rows with more than one file per language? how many rows have 0 files?
- [ ] What do the `G` / `PG` file prefixes and the `(C)` tag mean? (Ask gpinfo@ or infer from content.)
- [ ] Are there image-only scans in 2024–2026? (0.3)
- [ ] Copyright / redistribution and a no-objection email to gpinfo@ (owner decision; ADR-007)
- [ ] How the crawler gets the current `next-action` id (parse the JS chunk vs. a manual config value plus an alert)
