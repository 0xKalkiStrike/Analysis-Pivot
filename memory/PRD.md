# ExcelIntel — Product Requirements Document

## Original Problem Statement

Build an enterprise-grade, fully-offline Business Intelligence platform for Excel/CSV analytics — a Power BI alternative — in **pure Python** using PySide6, Polars, DuckDB, RapidFuzz, ReportLab, etc. No API keys, no cloud, no telemetry.

## User Personas

- **Data analyst** — cleans, dedupes, merges and validates spreadsheets across regions/departments.
- **Ops / finance manager** — imports invoices, checks GST/email validity, exports formatted Excel + PDF reports.
- **Data engineer** — runs SQL analytics via DuckDB console over raw sheets before ETL.
- **Auditor** — reviews duplicate/conflict reports with confidence + reason metadata.

## Core Requirements

1. Fully offline, Python-only, no external services.
2. Ingest .xlsx / .xls / .xlsm / .xlsb / .csv / .tsv.
3. High-performance engine (Polars + PyArrow + DuckDB) supporting millions of rows.
4. Smart multi-strategy duplicate detection with fuzzy algorithms + confidence + reason.
5. Intelligent cleaning (Unicode, whitespace, phones, emails).
6. Merge engine — inner/left/right/outer with conflict detection & resolution strategies.
7. Validation engine — invalid emails / phones / GSTINs / ZIPs / dates / outliers / missing headers.
8. Modern PySide6 desktop UI — dashboard, tabs, dockable panels, drag-and-drop, dark + light themes.
9. Analytics dashboard — KPI cards + bar/pie/line/scatter/histogram charts.
10. SQL console via DuckDB across loaded datasets.
11. Exports — formatted Excel, PDF, HTML, JSON.
12. Project workspaces (.eip) with save/load & recent projects.
13. CLI parity for headless workflows.
14. pytest unit + integration tests.
15. PyInstaller packaging scripts.

## What's Been Implemented (2026-01-30)

- ✅ Complete clean-architecture project layout under `/app/bi_platform`.
- ✅ Engines: Excel, Cleaning, Fuzzy (6 algorithms + soundex + jaccard + n-gram),
  Duplicate (exact/hash/column/fuzzy/smart with semantic column detection),
  Merge (all join types + 4 conflict-resolution strategies),
  Validation (email/phone/GST/ZIP/date/outliers/nulls with severity levels),
  Analytics (KPIs + column profiling).
- ✅ DuckDB manager (with SQLite fallback) — used in the SQL console.
- ✅ Export layer: styled XlsxWriter Excel, ReportLab PDF, HTML dashboard, JSON summary.
- ✅ Project service (.eip JSON files) with save/load and recent projects list.
- ✅ Desktop UI (PySide6): main window with menu + toolbar + status bar, dockable data-source
  explorer, tabbed workspace (Dashboard / Data / Duplicates / Validation / SQL / Charts),
  merge wizard dialog, virtualised Polars→Qt table model, dark & light QSS themes,
  drag-and-drop file loading, threaded background loader.
- ✅ Rich-powered CLI (`python -m bi_platform.cli`) with subcommands
  scan / info / duplicates / merge / validate / summary / export-report.
- ✅ Sample data generator (`scripts/generate_samples.py`) — customers + invoices + products
  with intentional duplicates, typos, invalid rows and conflicts.
- ✅ 28 pytest tests covering excel loading, fuzzy, duplicate, merge, validation, analytics, export.
- ✅ PyInstaller build helper (`scripts/build.py`).
- ✅ README.md + docs/INSTALL.md + screenshots in `docs/`.

### Verified end-to-end (headless)

- Loaded 4 sample sheets → 1,538 rows.
- Detected 15 duplicate groups in customers_region_a with confidence + reason metadata.
- Outer-joined the two customer regions → 540 rows, 30 conflicts.
- Validation produced 75 issues, quality score 94.4.
- DuckDB console executed `GROUP BY country` on registered dataset.
- Report generator wrote HTML + PDF + JSON + Excel packages successfully.
- PySide6 UI booted headlessly (`QT_QPA_PLATFORM=offscreen`) with populated dashboard, data table,
  duplicate table and validation table screenshots captured to `docs/`.

## Backlog / P0..P2

### P0 (next)

- Relationship auto-discovery between sheets (FK inference by column-name + value overlap).
- Bookmarks / saved views persisted in `.eip` projects.
- Real-time file watch → auto-refresh datasets.

### P1

- Drill-through cross-filtering between dashboard charts and tables.
- Pivot table builder UI.
- Custom measures / calculated columns (safe expression evaluator).
- Multi-sheet auto-loader with progress per sheet.

### P2

- Plugin loader from `~/.excelintel/plugins/*.py`.
- Localisation (i18n).
- CSV export with encoding options.
- Excel formula parser / repair.

## Environment Notes

- Environment is a Linux container without a physical display; the desktop app was validated
  headlessly using `QT_QPA_PLATFORM=offscreen` and screenshots were captured.
- No 3rd-party APIs, no LLMs, no cloud — 100% offline.
- Python 3.11 (works on 3.10–3.13).
