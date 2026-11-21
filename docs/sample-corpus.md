# Sample corpus and font inventory

- **Checked:** 2026-11-21 (issue #3, plan item 0.3). Builds on [source-notes.md](source-notes.md).
- **What it's for:**
  - test fixtures for the Phase 2 extractor (Unicode → legacy-font mapping → OCR → `low_confidence`)
  - the font list the legacy→Unicode converter has to cover
  - a better page estimate for capacity planning (0.4)
- **Method:**
  - listed every Extraordinary Gazette from 2024-01-01 to 2026-11-16 (8,175 rows) in month-sized windows
  - picked 26 PDFs (20 needed, plus extras) by category with a fixed random seed
  - downloaded them at ≥ 2.5 s per request with the project User-Agent
  - parsed each with a small standard-library script (no new dependency): pages, text operators, images,
    producer, and `/BaseFont` names with the `ABCDEF+` subset prefix stripped
  - also re-used the 12 PDFs from the recon, so the font inventory covers **38 PDFs**

## Fixture decision

**Reference by URL + SHA-256. Don't commit the PDFs** until the copyright / no-objection question is answered
(an email to gpinfo@ is drafted; see source-notes §1).
- `.gitignore` already blocks `*.pdf` outside `apps/ingest/tests/fixtures/`.
- Phase 2 tests will download a fixture into a local cache on first run and **fail if the SHA-256 differs**. A
  changed hash means the site re-uploaded the file; that's worth knowing, not silently accepting.
- If the answer is "no objection", we can commit a small subset (≤ 5 MB) under `apps/ingest/tests/fixtures/`.

## Coverage of the 0.3 categories

| Category | Covered by (# in the table below) | Notes |
|---|---|---|
| Unicode Sinhala | 3, 5, 7, 8, 10, 11, 15, 20, 24, 25, 26 | Iskoola Pota; Arial Unicode MS in Publisher/Distiller files |
| Legacy-font Sinhala (≥ 2 fonts) | 1, 13, 14, 18, 21 (legacy only); 9, 12, 19, 23 (mixed) | FMAbhayax + FMAbabld |
| Scanned / image-only | **none found** | All 38 PDFs have real text. See "Scans" below. |
| English | 2, 4, 6, 16, 17 | |
| Table-heavy | 13 (Customs rates of exchange), 14 (land acquisition schedule), 3/4 (15–16 pages) | |
| Very large | 12 (**135 pages**), plus the 37-page English PDF from the recon | |
| Amendment / rescinding | 15, 16 | 317 of 8,175 descriptions mention amend/rescind/revoke/cancel |
| si+en pair | 1+2, 3+4, 5+6 (one pair per year) | |
| Extras | 17 (en only), 18 (si only), 19 (`PG` file), 20 (`(C)` file), 21 (Election), 22 (Tamil, font check), 26 (Land Title Settlement), 23–25 (random spares) | |

## Corpus

| # | Gazette | Date | Lang | Why it is in the corpus | Pages | KB | Producer | Sinhala fonts |
|---|---|---|---|---|---|---|---|---|
| 1 | 2380/13 | 2024-04-17 | si | si+en pair (2024) | 2 | 103 | Acrobat Distiller 15.0 | legacy FM only |
| 2 | 2380/13 | 2024-04-17 | en | si+en pair (2024) | 2 | 118 | Acrobat Distiller 15.0 | legacy FM only |
| 3 | 2450/69 | 2025-08-23 | si | si+en pair (2025); large, Publisher-made | 15 | 638 | Microsoft Publisher 2010 | Unicode only |
| 4 | 2450/69 | 2025-08-23 | en | si+en pair (2025) | 16 | 784 | Microsoft Publisher 2010 | Unicode only |
| 5 | 2502/34 | 2026-08-19 | si | si+en pair (2026) | 7 | 291 | Acrobat Distiller 15.0 | Unicode only |
| 6 | 2502/34 | 2026-08-19 | en | si+en pair (2026) | 6 | 256 | Acrobat Distiller 15.0 | Unicode only |
| 7 | 2405/36 | 2024-10-10 | si | Sinhala, 2024 (font/producer spread) | 2 | 155 | Acrobat Distiller 15.0 | Unicode only |
| 8 | 2397/17 | 2024-08-13 | si | Sinhala, 2024 (font/producer spread) | 6 | 203 | Acrobat Distiller 24.0 | Unicode only |
| 9 | 2444/07 | 2025-07-07 | si | Sinhala, 2025 (font/producer spread) | 2 | 217 | Adobe PDF Library 17.0 | Unicode + legacy FM |
| 10 | 2465/25 | 2025-12-06 | si | Sinhala, 2025 (font/producer spread) | 4 | 163 | Acrobat Distiller 15.0 | Unicode only |
| 11 | 2488/35 | 2026-05-13 | si | Sinhala, 2026 (font/producer spread) | 2 | 496 | Microsoft Publisher 2010 | Unicode only |
| 12 | 2495/06 | 2026-07-01 | si | **very large** (135 pages; local-authority notices, PG file) | 135 | 482 | Acrobat Distiller 25.0 | Unicode + legacy FM |
| 13 | 2422/01 | 2025-02-03 | si | table-heavy (Customs rates of exchange) | 3 | 102 | Adobe PDF Library 10.0.1 | legacy FM only |
| 14 | 2390/04 | 2024-06-24 | si | table/schedule (land acquisition) | 3 | 125 | Acrobat Distiller 15.0 | legacy FM only |
| 15 | 2460/48 | 2025-11-01 | si | amendment / rescinding | 2 | 163 | Acrobat Distiller 15.0 | Unicode only |
| 16 | 2465/10 | 2025-12-03 | en | amendment / rescinding | 1 | 118 | Acrobat Distiller 15.0 | Unicode only |
| 17 | 2391/22 | 2024-07-03 | en | English only; 14 images and ~50 embedded font subsets (pasted documents) | 8 | 844 | Acrobat Distiller 15.0 | legacy FM only |
| 18 | 2375/37 | 2024-03-15 | si | Sinhala only (no English version) | 10 | 129 | Acrobat Distiller 15.0 | legacy FM only |
| 19 | 2504/68 | 2026-09-03 | si | PG-prefixed file | 1 | 171 | Adobe PDF Library 17.0 | Unicode + legacy FM |
| 20 | 2501/49 | 2026-08-11 | si | (C)-tagged file | 3 | 169 | Adobe PDF Library 17.0 | Unicode only |
| 21 | 2408/18 | 2024-11-02 | si | Election Commission notice | 2 | 86 | Adobe PDF Library 10.0.1 | legacy FM only |
| 22 | 2412/35 | 2024-11-29 | ta | Tamil (out of scope; font check only) | 1 | 545 | Microsoft Publisher 2010 | Unicode only |
| 23 | 2403/06 | 2024-09-24 | si | spare | 1 | 84 | Adobe PDF Library 10.0.1 | Unicode + legacy FM |
| 24 | 2450/02 | 2025-08-18 | si | spare | 2 | 237 | Acrobat Distiller 15.0 | Unicode only |
| 25 | 2471/56 | 2026-01-16 | si | spare | 7 | 216 | Acrobat Distiller 15.0 | Unicode only |
| 26 | 2420/72 | 2025-01-24 | si | Land Title Settlement notice (~40% of corpus) | 7 | 609 | Microsoft Publisher 2010 | Unicode only |

### Source URLs and SHA-256

1. `e96c185f4dad0b315c1ac6a09a9b542210a32b0c1f456ca165f34708edef023d` — [2380-13_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2380-13_S_1784565845.pdf)
2. `37142a86750d7dfd67f5dede61f5f634be36e052a57cb2ceba87d4489cc741ff` — [2380-13_E.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2380-13_E_1784565845.pdf)
3. `103328092e4fca8babe26774867bad98e374045766f46e7db937497251255429` — [2450-69_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2450-69_S_1784567384.pdf)
4. `7efd5913dc2b6893cf917cb78bab2256e4eb0fe5d9070a649cd68a5e2a5f6ee0` — [2450-69_E.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2450-69_E_1784567384.pdf)
5. `c9e4fb32c186136188f9cdfb4daf845a105dfd1d40139279c4db0f54d76cd2e8` — [G 47708(S).pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/G%2047708(S)_1788840758.pdf)
6. `40f6a8bf5571706dd3511ead2698fef52f50c486d838b19126f81a7d88ef785d` — [G 47708(E).pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/G%2047708(E)_1788840770.pdf)
7. `56255e55e5f0638fe01e01cacf4db1aca3113285837ce94fe3e9f33dd9095827` — [2405-36_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2405-36_S_1784566317.pdf)
8. `0f0a6c04ba2f59197c752ee739dbae98c4d6835ddf9430eb8ebf53040139a0b7` — [2397-17_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2397-17_S_1784566132.pdf)
9. `00a6138522febe8302e67d4c8e889a10a7bff0fca7e1bcccb692f960d37ec9a6` — [2444-07_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2444-07_S_1784567191.pdf)
10. `34a8c9ede2e764db23f22898c46d3c278f7d458d5225455ae5401c3d2f673224` — [2465-25_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2465-25_S_1784567690.pdf)
11. `37bb6b8bff221c4e6938e020ac1d01da95cd8b7d3f37bfce04f2062a37a6d329` — [2488-35_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2488-35_S_1784568191.pdf)
12. `aae9ad5433b34efd6008448ddd9a237a000b5313e1ad0e3136f68a20d710fe24` — [PG7819(S).pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/PG7819(S)_1791196147.pdf)
13. `7f9ade6386690e78477188e4a918bc55d18c88f7dbba447429e62cf52db51f52` — [2422-01_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2422-01_S_1784566690.pdf)
14. `89930015daa44b30153acaf6f195068b01720d08f79f384d62bfd1cbba023eb2` — [2390-04_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2390-04_S_1784565987.pdf)
15. `13f2fd8df9a9ebbbed2cc8edbbcb245844e159fcde560b56d59ce8a88bd4d1e6` — [2460-48_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2460-48_S_1784567615.pdf)
16. `7a5d2336ebc8aa40f5e18a72b270bd9e045b794c19510735477a3b86e3ca0738` — [2465-10_E.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2465-10_E_1784567685.pdf)
17. `d27b9af2505b4ed84ea1c11ea37f9d03a8c9f9a8575f93489122f347014e1e33` — [2391-22_E.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2391-22_E_1784566005.pdf)
18. `0a6acd3259f3b4e53a8118ab1847f4d373f921651278221c392ed1b5c776357c` — [2375-37_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2375-37_S_1784565778.pdf)
19. `cddc7aedfba0722caabc4074d13576e280ed03c1a5e06051602bb58bf0956396` — [PG 7954 - Filling Vacancy - IV-B - (S) 66A(1)(b).pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/PG%207954%20-%20Filling%20Vacancy%20-%20IV-B%20-%20(S)%2066A(1)(b)_1788944197.pdf)
20. `21ec8a9388b0d047be93f30f1782dc0a642e8e40f5cf5e70022a8a0b6411f877` — [G47671 (S)(C)  [Sec. 38].pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/G47671%20(S)(C)%20%20%5BSec.%2038%5D_1789980975.pdf)
21. `5330f40d85b7921f43a922b47d0452b0a649a9c499fec5ef9f50adc2e51ce7d1` — [2408-18_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2408-18_S_1784566376.pdf)
22. `e3da77b898cd5d460c092bb0848c142b5d13b4bf6d9f0bc1b9dc6cc9c547f928` — [2412-35_T.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2412-35_T_1784566438.pdf)
23. `1e983a9b138b83b361c59b1ca28cc8aeb11212eeed44d5f0751e12d08951640c` — [2403-06_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2403-06_S_1784566258.pdf)
24. `cd254ed5c1d96d5048dc9eb9351f0f442db4d85f8e29fe53a1d10b8c5a5fee7f` — [2450-02_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2450-02_S_1784567357.pdf)
25. `e78f53020e6bb220fdace5979d093a9838df8e95431bc543995ae22eb730ad09` — [2471-56_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2471-56_S_1784567856.pdf)
26. `65bd0aaa72cf7cbad788b8684020084c0e1eb3fd33feef7c5e77c89ecd5089a6` — [2420-72_S.pdf](https://documents.gov.lk/api/content-file-proxy?file=/extra-gazette-content/2420-72_S_1784566656.pdf)

## Font inventory (38 PDFs)

Names are normalised: the subset prefix and the `*…-NNNNN-Identity-H` suffix are stripped, and weight/style
suffixes are merged.

| Font family | PDFs | Class | Converter action |
|---|---|---|---|
| IskoolaPota (`Iskoola Pota`, `-Bold`) | 30 | **Unicode Sinhala** | none; read the text as-is, then NFC |
| ArialUnicodeMS | 11 | Unicode, multi-script | none |
| **FMAbabld** (`FMAbabldBold`) | 16 | **Legacy Sinhala (FM)** | map with the FM table |
| **FMAbhayax** | 13 | **Legacy Sinhala (FM)** | map with the FM table |
| Latha | 6 | Unicode Tamil | none (Tamil is out of scope for now) |
| aAvarangal | 3 | **Unknown, likely legacy Tamil** | flag; Tamil is out of scope |
| GP Rasanji | 1 (Tamil PDF) | **Unknown** | flag; check whether it's Sinhala or Tamil |
| TimesNewRoman (all PS/MT variants), Times | 38 | Latin | none |
| MinionPro, Calibri, CourierNew, Arial, Verdana, ComicSansMS, Cambria, Tahoma | 1–5 each | Latin | none |

**How Sinhala PDFs split** (the 20 Sinhala PDFs in this corpus):

| Class | PDFs |
|---|---|
| Unicode only | 11 |
| legacy FM only | 5 |
| Unicode + legacy FM in the same file | 4 |

**Takeaways for Phase 2**
1. **Legacy text is common, not an edge case.** A quarter of the Sinhala PDFs here have **no Unicode Sinhala at
   all**: 2380/13, 2422/01, 2390/04, 2375/37 and 2408/18 (all Distiller or PDF Library 10). The FM→Unicode
   converter is on the critical path.
2. **Decide per text span.** Mixed files put Iskoola Pota headings next to FMAbhaya body text, so the
   extractor has to choose the converter by each span's font, not by page or file.
3. **English PDFs contain FM fonts too** (FMAbabldBold in 2380/13-en and in recon PDFs). Run the same span
   logic on English files, because the Sinhala headers would otherwise come out as mojibake.
4. **The converter only needs one FM family so far.** Every legacy span in 38 PDFs is FMAbhaya (regular `x`) or
   FMAbabld (bold), both from the same FM family. Unknown fonts must be logged, and their pages marked
   `low_confidence`.
5. **Scans:** there were none in 38 PDFs, and every file has text operators (lowest: 41 on a 1-page notice).
   That's good news for OCR cost. Still, keep the OCR fallback:
   - 2391/22 (en) has 14 images over 8 pages, and may contain scanned pages or maps
   - older years or unusual notices may be scans
   - Phase 2 should log "page has images but no text" so we learn the real rate.
6. Tamil, for later: Latha is Unicode, and `aAvarangal` / `GP Rasanji` need checking.

## Listing facts from the full 2024+ pass (8,175 rows)

These answer the open questions in source-notes §9:

| Question | Answer |
|---|---|
| Is offset paging safe? | **No.** Over the whole range, pagination returned 82 rows twice and **silently skipped 82 others**, because rows with the same date have no stable order. **The crawler must list in date windows that fit in one page** (a month with `limit=400`, split into halves when a month is bigger, e.g. Jul 2026 had 468). |
| Is `(gazette_no, sub_no)` unique? | **No.** 22 numbers appear on more than one row (different site `id`s): duplicate entries with 0 files, the same gazette re-entered with a new description, and even different dates (`2491/04`: 3 Jun vs 1 Jul 2026). **The primary key is the site `id`**, with `(no, sub)` indexed but **not** unique. A de-dup rule is needed (prefer the row with files, then the newest `updatedAt`). |
| Rows with 0 files? | 122 (1.5 %). Store them and retry later. |
| More than one file per language? | 1 row (2507/90), which carries **`.epub` copies** next to the PDFs. Filter by `.pdf`. |
| Language mix | si+ta+en 6,901 · si+en 732 · si only 151 · ta only 114 · en only 88 · si+ta 50 · en+ta 16 · none 122 |
| 3-digit sub-numbers | 114 rows (`NNNN/NNN`) |
| Descriptions | 54 are just the number; 79 differ between the language fields; keywords are empty in all 8,175 |
| `updatedAt` lag | often **more than 2 weeks** after `date` (up to about 25 days in the same-month count). The daily re-list window should be **30 days**, not 14 (source-notes §8 updated). |

**Issuers** (top descriptions before " - "): Land Title Settlement Dept. ≈ **3,500 rows (≈ 43 %)** under at
least 5 spellings · Land Acquisition ≈ 840 (spelt "Aquisition", "Aquation", …) · Election(s) Commission ≈ 550 ·
Presidential Secretariat 164 · Ministry of Labour 141 · Sri Lanka Customs 137.
- **Department normalisation is mandatory** (PRD review item 17). Spelling variants are everywhere.
- **Privacy (ADR-007):** Land Title Settlement and Land Acquisition notices are about half of the corpus. They
  name land owners and claimants. That makes the name-search and indexing decisions in ADR-007 central, not
  marginal.

## Page estimate, refined

- **38 PDFs:** median 3 pages, mean 8.1. The mean is skewed by deliberate picks (135, 37, 16, 15 pages).
- **The 12 random recon PDFs:** median 2, mean 4.9.
- **Keep the 45k–75k page range for ≈ 15,000 si+en PDFs, but plan for a long tail.** Single gazettes run to 100+
  pages, so the ingest job needs a page cap per run and per-page commits.
- 0.4 should use **5 pages/PDF as the base case and 8 as the high case**.
