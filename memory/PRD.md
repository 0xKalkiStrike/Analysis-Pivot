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

## What's Been Implemented (2026-01-30 · v1.1)

- ✅ Complete clean-architecture project layout under `/app/bi_platform`.
- ✅ Engines: Excel, Cleaning, Fuzzy (6 algorithms + soundex + jaccard + n-gram),
  Duplicate, Merge (all join types + 4 conflict-resolution strategies),
  Validation, Analytics, **Relationship (FK inference)**, **Pivot (9 aggregations)**.
- ✅ DuckDB manager (SQLite fallback) — used in the SQL console.
- ✅ Export layer: styled XlsxWriter Excel, ReportLab PDF, HTML dashboard, JSON summary.
- ✅ Services: Project (.eip), **SavedView (workspace snapshots)**, **FileWatcher (live refresh with debounce)**.
- ✅ Desktop UI (PySide6):
    - Main window with menu + toolbar + status bar, docked Data Sources (left) and Saved Views (right).
    - **8 tabs**: Dashboard, Data, Duplicates, Validation, **Pivot**, **Relationships**, SQL, Charts.
    - Drag-and-drop pivot builder with Fields → Rows / Columns drop-zones.
    - Relationship graph (PyQtGraph) + table with cardinality + confidence.
    - Saved-Views panel: save current tab/dataset/filters/pivot/SQL and one-click restore.
    - Live-refresh toggle (menu + toolbar) that auto-reloads changed source files.
    - Merge wizard dialog, virtualised Polars→Qt table model, dark & light QSS themes,
      drag-and-drop file loading, threaded background loader.
- ✅ Rich-powered CLI (`python -m bi_platform.cli`) with subcommands
  scan / info / duplicates / merge / validate / summary / export-report.
- ✅ Sample data generator with intentional duplicates, typos, invalid rows and conflicts.
- ✅ **39 pytest tests** — engines (Excel, fuzzy, duplicate, merge, validation, analytics,
  export, pivot, relationship, saved-view).
- ✅ PyInstaller build helper (`scripts/build.py`).
- ✅ README.md + docs/INSTALL.md + 6 UI screenshots in `docs/`.

### Verified end-to-end (headless, 2026-01-30)

- Loaded 4 sample sheets → 1,538 rows.
- Pivot: `invoices_2024` cross-tab `status × product` sum(total) → 4 rows × N product columns.
- Relationships: discovered 3 links (customer_id/customer_id N:1 @ 99% confidence + 2 N:N links).
- Saved Views: captured "Invoice Pivot" and "Region A Duplicates" views (roundtrip verified).
- Live Refresh: watched 4 files; simulated `os.utime` triggered the debounced reload and
  the affected sheet was re-parsed and re-rendered.
- Detected 15 duplicate groups, outer-merge with 30 conflicts, validation score 94.4.
- DuckDB SQL console executed `GROUP BY country`.
- Report generator wrote HTML + PDF + JSON + Excel packages.

## Backlog / P0..P2

### P0 (next)

- Cross-filtering between dashboard charts and tables (click a bar → filter data).
- Custom measures / calculated columns (safe expression evaluator).

### P1

- Pivot table drill-through (double-click a cell → underlying rows).
- Multi-sheet auto-loader with progress per sheet.
- Command palette (Ctrl+P) global search across actions, files and views.

### P2

- Plugin loader from `~/.excelintel/plugins/*.py`.
- Localisation (i18n).
- Excel formula parser / repair.
- Multi-monitor workspace persistence.

## Environment Notes

- Environment is a Linux container without a physical display; the desktop app was validated
  headlessly using `QT_QPA_PLATFORM=offscreen` and screenshots were captured.
- No 3rd-party APIs, no LLMs, no cloud — 100% offline.
- Python 3.11 (works on 3.10–3.13).
