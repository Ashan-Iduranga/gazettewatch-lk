# ADR-008: Embedding model and vector dimension

- **Status:** Proposed (owner decides)
- **Date:** 2026-11-21

## Context
- Ask and hybrid search need one multilingual embedding model for Sinhala, English and Singlish queries
  against Sinhala and English gazette chunks.
- The model ID and the dimension fix the `chunks.embedding` column type, the HNSW index and most of the DB size.
- [capacity.md](../planning/capacity.md) shows that vectors plus HNSW are about 25–55 % of the database,
  depending on the dimension. The full 2024 → now range is over the Supabase Free 500 MB at any dimension.
- **Measured:** pages average 2.8 KB / 1,736 characters (≈ 1,000 tokens by our assumption); 2.8 % are over 8 KB.
- **Constraints:**
  - LLM calls are server-side only (CLAUDE.md)
  - free tiers while building; a paid Gemini tier before launch (PRD)
  - pgvector HNSW supports up to 2,000 dims for `vector` and 4,000 for `halfvec`

## Options considered

| # | Model | Dims / type | Per-chunk storage (vector + HNSW) | DB, 2024 → now (base) | Notes |
|---|---|---|---|---|---|
| 1 | `gemini-embedding-2` | **768 `halfvec`** | ≈ 3.4 KB | ≈ 1.1 GB | 8,192-token input (no page splitting needed in practice), truncated outputs are normalised, $0.20 / 1M tokens |
| 2 | `gemini-embedding-2` | 768 `vector` | ≈ 6.6 KB | ≈ 1.4 GB | full float32; ~2× the space of option 1 for a negligible recall gain |
| 3 | `gemini-embedding-2` | 1536 `halfvec` | ≈ 6.6 KB | ≈ 1.4 GB | maybe a little better recall; double the vector space of option 1 |
| 4 | `gemini-embedding-2` | 3072 `halfvec` | ≈ 13 KB | ≈ 1.9 GB | the full dimension; too large for our budget |
| 5 | `gemini-embedding-001` | 768 `halfvec` | ≈ 3.4 KB | ≈ 1.1 GB | $0.15 / 1M, but only a 2,048-token input (long pages must be split) and truncated outputs must be normalised by hand; older model |
| 6 | open-source multilingual model (self-hosted) | 384–1024 | varies | varies | no API cost, but needs a GPU or slow CPU inference in Actions; adds a dependency and ops work |

The prices and limits were checked on 2026-11-21 (sources in capacity.md). Sinhala quality has not been measured
for any option yet.

## Decision
**Proposed: option 1, `gemini-embedding-2` at 768 dimensions stored as `halfvec(768)`, cosine distance, HNSW
(m = 16, ef_construction = 64).**
- It is the smallest storage that still uses a recommended output size, so it fits the rolling-12-month free-tier
  plan in capacity.md (≈ 316 MB).
- The 8k-token input means one chunk per page almost always.
- Normalised truncation avoids an extra step.
- It's the same vendor as the answer model, so it uses one key and one bill.

*Owner to confirm or choose another option.*

## Consequences
- **Schema:**
  - `chunks.embedding halfvec(768) not null`
  - `chunks.embedding_model text not null`, e.g. `'gemini-embedding-2@768'`, in every row
  - `CREATE INDEX … USING hnsw (embedding halfvec_cosine_ops)`
- **The query embedding must use the same model and dimension,** with task types: `RETRIEVAL_DOCUMENT` for
  chunks and `RETRIEVAL_QUERY` for queries.
- **Re-embed strategy** (when switching model or dimension):
  1. add a new column `embedding_v2` (or a `chunk_embeddings(model, chunk_id, embedding)` table)
  2. backfill it in the background
  3. build its HNSW index
  4. switch the query path with a config flag
  5. drop the old column

  At about $9–17 per full re-embed this is cheap. Time and quota are the real cost.
- **Risk: Sinhala/Singlish recall is unknown.** Phase 6 eval questions must include Sinhala and Singlish. If recall
  is weak, try 1536 dims (option 3) on the eval set before changing models. Hybrid search (trigram + exact gazette
  number) covers part of this gap.
- **Risk: free-tier rate limits are unofficial and low.** The backfill needs the paid tier (a one-off, owner
  approval, budget cap). Daily volume (~80 chunks) fits the free tier.
- **Prompt and model IDs are logged with each trace** (PRD review NFR: LLM observability).
