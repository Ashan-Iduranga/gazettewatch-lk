# GazetteWatch LK

Search and ask questions about Sri Lankan government Extraordinary Gazettes in **Sinhala or English** — every answer cites the gazette number, date and page, with a link to the official PDF on [documents.gov.lk](https://documents.gov.lk).

> 🚧 Work in progress. Not legal advice and not an official source.

## Planned features
- Search by words, gazette number, date and department
- Ask questions in Sinhala or English with citations
- Legacy Sinhala font conversion to Unicode, with OCR fallback
- Daily automatic updates
- Optional account for saved searches and email alerts — anonymous by default

## Stack
Next.js · FastAPI · Supabase (Postgres, pgvector, pg_trgm, Auth) · Gemini · GitHub Actions · Vercel · Render

## Docs
- [Product requirements](docs/PRD.md)
- [Architecture decisions](docs/adr/)
- [PRD review & Phase 0–1 plan](docs/planning/prd-review.md)

_Live demo, architecture diagram, evaluation results and setup instructions will be added as the project is built._
