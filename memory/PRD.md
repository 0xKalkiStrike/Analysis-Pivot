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

## What's Been Implemented (2026-01-30 · v1.2)

- ✅ Complete clean-architecture project layout under `/app/bi_platform`.
- ✅ Engines: Excel, Cleaning, Fuzzy (6 algorithms + soundex + jaccard + n-gram),
  Duplicate, Merge, Validation, Analytics, Relationship (FK inference), Pivot (9 aggregations).
- ✅ DuckDB manager (SQLite fallback) — used in the SQL console.
- ✅ Export layer: styled XlsxWriter Excel, ReportLab PDF, HTML dashboard, JSON summary.
- ✅ Services: Project (.eip), SavedView (workspace snapshots), FileWatcher (live refresh with debounce).
- ✅ Desktop UI (PySide6):
    - Main window with menu + toolbar + status bar, docked Data Sources (left) and Saved Views (right).
    - 8 tabs: Dashboard, Data, Duplicates, Validation, Pivot, Relationships, SQL, Charts.
    - **Interactive dashboard** — clickable bar & pie charts with three cross-filter signals
      (`dataset_selected`, `quality_selected`, `top_value_selected`) plus a "Top values by column" chart.
    - **Drill-through** from any pivot cell via double-click → DrillThroughDialog showing filtered rows
      with breadcrumb, aggregate re-computation and Excel export.
    - **Command Palette (Ctrl+P)** — fuzzy-search over Actions / Navigate / Dataset / View / File
      categories, arrow-key navigation, Enter to run.
    - Drag-and-drop pivot builder, relationship graph, saved-views panel, live-refresh toggle,
      merge wizard, dark & light QSS themes.
- ✅ Rich-powered CLI (`python -m bi_platform.cli`).
- ✅ Sample data generator with intentional duplicates, typos, invalid rows and conflicts.
- ✅ **47 pytest tests** — engines + drill-through logic + command palette scoring.
- ✅ PyInstaller build helper (`scripts/build.py`).
- ✅ README.md + docs/INSTALL.md + 10 UI screenshots in `docs/`.

### Verified end-to-end (headless, 2026-01-30)

- Loaded 4 sample sheets → 1,538 rows.
- Cross-filter: clicking the "Duplicates" pie slice jumped to the Duplicates tab and auto-ran
  detection (15 groups, 35 rows flagged). Status bar shows "Filtered by quality segment: Duplicates".
- Drill-through: pivot cell `status=paid × product=About` opened DrillThroughDialog showing 1 row
  with recomputed `sum(total) = 8637.30` and Export Rows button.
- Command Palette: `merge` → "Merge Wizard" first, `invoices` → the invoice dataset activation
  command first (with row/col hint). Fuzzy typo tolerated (`reltionships` → Discover Relationships).
- Pivot cross-tab, relationship graph (99%-confidence FK), saved-view roundtrip, live-refresh
  auto-reload — all continue to pass.

## Backlog / P0..P2

### P0 (next)

- Custom measures / calculated columns (safe expression evaluator).
- Multi-sheet auto-loader with progress per sheet.

### P1

- Plugin loader from `~/.excelintel/plugins/*.py`.
- Excel formula parser / repair.

### P2

- Localisation (i18n).
- Multi-monitor workspace persistence.
- Delta/incremental scan when a file changes (only re-read added rows).

## Environment Notes

- Environment is a Linux container without a physical display; the desktop app was validated
  headlessly using `QT_QPA_PLATFORM=offscreen` and screenshots were captured.
- No 3rd-party APIs, no LLMs, no cloud — 100% offline.
- Python 3.11 (works on 3.10–3.13).
