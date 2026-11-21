"""Capacity & cost model for GazetteWatch LK (plan item 0.4). All assumptions at the top; re-run to reproduce."""
MB = 1024 ** 2
# ---- corpus (source-notes.md, sample-corpus.md, measure_text.py on 26 PDFs / 250 pages) ----
GAZETTES = 8175
PDFS = 7835 + 7738                 # rows with si + rows with en (full 2024+ listing)
PAGES_PER_PDF = {"base": 4.9, "high": 8.0}   # random-sample mean / deliberate-corpus mean
TEXT_BYTES_PER_PAGE = 2805 + 270   # measured mean + FM->Unicode growth (7.7 % FM chars, 1 -> 3 bytes)
CHUNKS_PER_PAGE = 1.1              # page chunks; 2.8 % of pages > 8 KB get split
CHUNK_PREFIX = 150                 # "gazette no / date / department" metadata prefix per chunk
CHARS_PER_PAGE = 1736              # measured
CHARS_PER_TOKEN = 1.7              # assumption: Sinhala-heavy text tokenises denser than English (~4)
# ---- Postgres sizing assumptions ----
ROW_OVERHEAD = 60                  # tuple header + ids/ints/dates
BTREE_PER_ROW = 3 * 40             # ~3 btree indexes per table row
TRGM_GIN_FACTOR = 1.5              # pg_trgm GIN index size vs. indexed text (assumption; measure in Phase 2)
HNSW_NEIGHBOUR_BYTES = 200         # m=16: ~32 layer-0 neighbours x 6 B
HNSW_FACTOR = 1.1
# ---- limits / prices (checked 2026-11-21; see capacity.md for sources) ----
SUPABASE_FREE_DB = 500 * MB
EMBED_PRICE_PER_M = {"standard": 0.20, "batch": 0.10}       # gemini-embedding-2, text input
FLASH_PRICE_PER_M = {"2026 intro": (0.75, 3.75), "from 2027-01-01": (1.50, 7.50)}  # in, out
ACTIONS_FREE_MIN = 2000            # private repo, GitHub Free (docs also state it as $12 of compute)
FETCH_SECONDS = 2.5

def db_size(pages, dims, bytes_per_dim):
    chunks = pages * CHUNKS_PER_PAGE
    pages_tbl = pages * (TEXT_BYTES_PER_PAGE + ROW_OVERHEAD + BTREE_PER_ROW)
    chunk_text = pages * TEXT_BYTES_PER_PAGE + chunks * CHUNK_PREFIX
    chunks_tbl = chunk_text + chunks * (ROW_OVERHEAD + BTREE_PER_ROW)
    vec = chunks * (bytes_per_dim * dims + 8)
    hnsw = chunks * (bytes_per_dim * dims + 8 + HNSW_NEIGHBOUR_BYTES) * HNSW_FACTOR
    trgm = chunk_text * TRGM_GIN_FACTOR
    gazettes = GAZETTES * 2 * 600     # gazette + file rows with metadata
    parts = {"pages": pages_tbl, "chunks text": chunks_tbl, "vectors": vec, "hnsw": hnsw, "trigram gin": trgm, "gazettes/files": gazettes}
    return parts, sum(parts.values())

configs = [("vector(768)", 768, 4), ("halfvec(768)", 768, 2), ("halfvec(1536)", 1536, 2), ("halfvec(3072)", 3072, 2)]
print("## DB size (MB) vs Supabase Free 500 MB")
print("| case | pages | chunks | " + " | ".join(c[0] for c in configs) + " | text-only (no vectors) |")
print("|---|---|---|" + "---|" * (len(configs) + 1))
for case, ppp in PAGES_PER_PDF.items():
    pages = PDFS * ppp
    cells = []
    for name, d, b in configs:
        parts, total = db_size(pages, d, b); cells.append(f"{total / MB:,.0f}")
    parts, total = db_size(pages, 768, 2)
    text_only = total - parts["vectors"] - parts["hnsw"]
    print(f"| {case} | {pages:,.0f} | {pages * CHUNKS_PER_PAGE:,.0f} | " + " | ".join(cells) + f" | {text_only / MB:,.0f} |")
parts, total = db_size(PDFS * PAGES_PER_PDF["base"], 768, 2)
print("\nbreakdown base / halfvec(768):", {k: f"{v / MB:,.0f} MB" for k, v in parts.items()})

print("\n## Embedding backfill")
for case, ppp in PAGES_PER_PDF.items():
    pages = PDFS * ppp; chunks = pages * CHUNKS_PER_PAGE
    tokens = pages * CHARS_PER_PAGE / CHARS_PER_TOKEN + chunks * CHUNK_PREFIX / CHARS_PER_TOKEN
    print(f"{case}: {chunks:,.0f} chunks, {tokens / 1e6:,.1f} M tokens -> ${tokens / 1e6 * EMBED_PRICE_PER_M['standard']:,.2f} standard / ${tokens / 1e6 * EMBED_PRICE_PER_M['batch']:,.2f} batch;"
          f" at 1,000 requests/day (unofficial free RPD, 1 chunk/request) = {chunks / 1000:,.0f} days")
daily_chunks = 15 * PAGES_PER_PDF["base"] * CHUNKS_PER_PAGE
print(f"daily new: ~{daily_chunks:,.0f} chunks/day (fits any free quota)")

print("\n## GitHub Actions minutes")
fetch_min = PDFS * FETCH_SECONDS / 60
proc_min = PDFS * PAGES_PER_PDF["high"] * 0.05 / 60      # PyMuPDF ~0.05 s/page
setup_min_per_run = 3                                   # checkout, uv sync, tesseract-sin install
runs = 3                                                # <= 5 h each
backfill = fetch_min + proc_min + runs * setup_min_per_run + 60  # +60 min for listing, retries, embedding waits
daily = 3 + (35 + 15) * FETCH_SECONDS / 60 + 1
print(f"backfill: {fetch_min:,.0f} min fetching + {proc_min:,.0f} min processing -> ~{backfill:,.0f} min in {runs} runs")
print(f"daily run: ~{daily:,.1f} min (rounded up per job) -> ~{30 * round(daily + 0.5):,.0f} min/month")
print(f"month with backfill: ~{backfill + 30 * round(daily + 0.5):,.0f} of {ACTIONS_FREE_MIN} free min")

print("\n## /ask cost per question (8 chunks of context)")
in_tok = 8 * (CHARS_PER_PAGE / CHARS_PER_TOKEN) + 1200      # chunks + system prompt + question
out_tok = 500
for k, (pi, po) in FLASH_PRICE_PER_M.items():
    c = in_tok / 1e6 * pi + out_tok / 1e6 * po
    print(f"{k}: ~{in_tok:,.0f} in + {out_tok} out tokens = ${c:.4f}/question; 1,000 questions = ${c * 1000:,.2f}")

print("\n## Other")
print(f"PDF download total: ~{PDFS * 250 / 1024 / 1024:,.1f} GB (not stored in DB; Actions cache 10 GB/repo)")
print(f"OCR allowance (2 % of pages, 0 scans seen in 38 PDFs): ~{PDFS * PAGES_PER_PDF['base'] * 0.02:,.0f} pages")

print("\n## Scenarios to fit Supabase Free (halfvec(768), base pages)")
def lean(pages):
    # store page text once (chunks = page text + prefix; no separate pages.text copy)
    parts, _ = db_size(pages, 768, 2)
    parts.pop("pages"); parts["pages (meta only)"] = pages * (ROW_OVERHEAD + BTREE_PER_ROW)
    return parts, sum(parts.values())
windows = {"2024-01 -> now (35 months)": 1.0, "2025-01 -> now (23 months)": (2973 + 2651) / 8175,
           "rolling 12 months": 12 / 35, "rolling 6 months": 6 / 35}
print("| window | gazettes | standard schema MB | lean schema MB | fits 500 MB (lean, 20 % headroom)? |")
print("|---|---|---|---|---|")
for w, frac in windows.items():
    pages = PDFS * PAGES_PER_PDF["base"] * frac
    _, std = db_size(pages, 768, 2); _, ln = lean(pages)
    print(f"| {w} | {GAZETTES * frac:,.0f} | {std / MB:,.0f} | {ln / MB:,.0f} | {'yes' if ln < 0.8 * SUPABASE_FREE_DB else 'no'} |")
growth = 30 * 15 * PAGES_PER_PDF["base"]
_, g = lean(growth)
print(f"growth: ~{g / MB:,.0f} MB/month (lean)")
