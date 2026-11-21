# ADR-007: Personal data in gazette text

- **Status:** Proposed (owner decides; PDPA points to be checked in 0.9)
- **Date:** 2026-11-21

## Context
- Extraordinary Gazettes are official public notices, but many name private people:
  - **Land Title Settlement** notices are ≈ 43 % of 2024+ gazettes ([sample-corpus.md](../sample-corpus.md))
  - Land Acquisition notices are ≈ 10 %
  - appointment, court and election notices also name people
  - they include names, addresses, land lots, and sometimes NIC numbers
- GazetteWatch makes this text **easier to find** than the source does. The source only has a number/date list
  plus PDFs; we add full-text search across all of them. That changes the privacy risk, even though each document
  is already public.
- The rules already in force:
  - CLAUDE.md: mask NIC, phone and email before logging or calling the LLM; no personal data in logs; never send
    account data to the LLM
  - Answers must quote and cite the retrieved chunks, and **the chunks are the evidence**
- Sri Lanka's PDPA (No. 9 of 2022) applies to processing personal data. Its core duties start on 1 Jan 2027 (PRD).
  Whether a "publicly available official publication" exemption applies, and what it covers, **is to be checked in
  0.9**. This ADR doesn't rely on an exemption.

There are four decisions here.

### (a) Personal data in what we send the LLM
1. **Send chunks as-is.** Pros: answers can quote names and numbers exactly. Cons: personal data goes to an overseas
   processor; it conflicts with the masking rule.
2. **Mask NIC, phone and email in chunks before the LLM, and keep names.** Pros: removes the high-risk identifiers;
   names stay, so an answer about a notice is still useful. Cons: masked values can't be quoted. The user sees them
   in the cited page instead.
3. **Mask names too** (NER). Cons: Sinhala NER is weak, and the answers stop making sense (e.g. "who was appointed").

### (b) Searching by a person's name
1. **Allowed, like any other text.** Pros: simple, and useful (people check their own land notices). Cons: makes
   profiling a person across gazettes easy.
2. **Allowed, with limits:** no name autocomplete or suggestions, no "all gazettes about this person" view, results
   are rate-limited like everything else, and person names are kept out of logs and analytics.
3. **Blocked** (detect name-only queries). Cons: can't be done reliably in Sinhala, and blocks real needs.

### (c) Search-engine indexing of our gazette pages
1. **Index them.** Pros: discoverability, SEO. Cons: puts names into Google results under our domain; hard to undo.
2. **`noindex` on gazette and search pages; index only the home and about pages.** Pros: we don't widen exposure
   beyond the source. Cons: less traffic.

### (d) Retention and removal
1. **Mirror the source.** Keep text while the gazette is on documents.gov.lk; when a re-crawl finds it removed,
   delete our copy, chunks and vectors within 7 days. Also provide a contact route for removal requests.
2. **A fixed period** (e.g. a rolling 12 months, which also matches capacity.md option A).

## Decision
**Proposed (privacy-first defaults for v1):**
- **(a) Option 2:** mask NIC, phone and email patterns in chunk text before every LLM call and in all logs and
  traces (Langfuse input masking on). Names stay.
  - The displayed page text stays verbatim, because it's the official record and the citation target.
  - The masking runs **after retrieval and before the prompt**, so search can still match exact NIC/lot numbers.
- **(b) Option 2:** name search works as normal text search, but there's no person-oriented UI, autocomplete or
  suggestions. Query text isn't stored unless the user turned history on.
- **(c) Option 2:** `noindex` (meta tag + `X-Robots-Tag`) on `/gazette/*`, `/search`, `/ask`. `robots.txt` allows
  only public static pages.
- **(d) Option 1:** mirror the source; delete within 7 days of removal upstream. Add a contact address for removal
  requests, handled manually. This combines with any rolling window chosen in capacity.md.

*Owner to confirm each of (a)–(d).*

## Consequences
- **Ingest:** run a masking function (regex for NIC: old `\d{9}[VvXx]` and new `\d{12}`, plus Sri Lankan phone
  numbers and emails) as a tested pure function, used by the API before the LLM and by every logger.
  - Tests: Sinhala and English text, numbers inside tables, and false positives such as gazette numbers and lot
    numbers.
- **Ask:** answers may name people (from the cited chunk) but can't show masked identifiers. The UI shows a note:
  "Some numbers are hidden in answers; see the cited page."
- **The threat model (0.8)** adds "profiling a person via search" and "personal data leaking into traces".
- **Privacy notes (0.9):**
  - list gazette-derived personal data as a separate category (source: public official publication; purpose:
    search of public notices; processor: Gemini for masked chunks only; retention: mirror the source)
  - verify the PDPA position
- **Web:** `noindex` headers are needed from the first deploy (1.11), because removing indexed pages later is slow.
- **Revisit** after the gpinfo@ reply and before public launch.
