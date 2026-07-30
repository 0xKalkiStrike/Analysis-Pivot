"""ExcelIntel command-line interface — headless BI operations.

Usage:
    python -m bi_platform.cli scan <folder>
    python -m bi_platform.cli info <file> [--sheet SHEET]
    python -m bi_platform.cli duplicates <file> [--sheet SHEET] [--column COL] [--threshold 88]
    python -m bi_platform.cli merge <left> <right> --on KEY [--how inner]
    python -m bi_platform.cli validate <file> [--sheet SHEET]
    python -m bi_platform.cli summary <folder>
    python -m bi_platform.cli export-report <folder> [--out reports/]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .core.logger import setup_logging
from .engine import (AnalyticsEngine, CleaningEngine, DuplicateEngine,
                     ExcelEngine, MergeEngine, ValidationEngine)
from .export import ExcelExporter, ReportGenerator
from .models import Dataset

console = Console()


def _print_df(df, title: str, max_rows: int = 15) -> None:
    if df is None or (hasattr(df, "is_empty") and df.is_empty()):
        console.print(f"[yellow]{title}: (empty)[/yellow]")
        return
    table = Table(title=title, expand=False, show_lines=False)
    for c in df.columns:
        table.add_column(str(c), overflow="fold")
    for row in df.head(max_rows).iter_rows():
        table.add_row(*[("" if v is None else str(v))[:60] for v in row])
    console.print(table)


def cmd_scan(args: argparse.Namespace) -> int:
    eng = ExcelEngine()
    files = eng.scan_folder(args.folder, recursive=not args.no_recursive)
    table = Table(title=f"Discovered files in {args.folder}")
    table.add_column("File"); table.add_column("Size (KB)", justify="right"); table.add_column("Sheets")
    for f in files:
        try:
            sheets = eng.list_sheets(f)
        except Exception as e:
            sheets = [f"<error: {e}>"]
        table.add_row(str(f), f"{f.stat().st_size / 1024:.1f}", ", ".join(sheets))
    console.print(table)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    ds = ExcelEngine().load_sheet(args.file, sheet_name=args.sheet)
    console.print(f"[bold]{ds.name}[/bold]  —  {ds.rows:,} rows × {ds.cols} cols")
    schema = [{"column": c, "dtype": str(ds.df.schema[c]),
               "nulls": ds.df[c].null_count(), "unique": ds.df[c].n_unique()}
              for c in ds.columns]
    import polars as pl
    _print_df(pl.DataFrame(schema), "Schema")
    _print_df(ds.df, "Preview")
    return 0


def cmd_duplicates(args: argparse.Namespace) -> int:
    ds = ExcelEngine().load_sheet(args.file, sheet_name=args.sheet)
    if args.clean:
        ds = CleaningEngine().clean(ds)
    engine = DuplicateEngine()
    if args.column:
        groups = engine.detect_fuzzy(ds, args.column, threshold=args.threshold)
    else:
        groups = engine.detect_smart(ds, threshold=args.threshold)
    console.print(f"Detected [bold]{len(groups)}[/bold] duplicate groups "
                  f"({sum(g.size for g in groups)} rows involved).")
    df = engine.to_dataframe(groups)
    _print_df(df, "Duplicate Report", max_rows=30)
    if args.out:
        ExcelExporter().export_duplicates(groups, args.out)
        console.print(f"[green]Written {args.out}[/green]")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    l = ExcelEngine().load_sheet(args.left, sheet_name=args.left_sheet)
    r = ExcelEngine().load_sheet(args.right, sheet_name=args.right_sheet)
    result = MergeEngine().merge(l, r, on=args.on.split(","), how=args.how)
    console.print(
        f"Matched: [bold green]{result.matched}[/bold green]  "
        f"Unmatched L: {result.unmatched_left}  R: {result.unmatched_right}  "
        f"Conflicts: [yellow]{len(result.conflicts)}[/yellow]"
    )
    _print_df(result.dataset.df, "Merged preview")
    if args.out:
        ExcelExporter().export_dataset(result.dataset, args.out)
        console.print(f"[green]Written {args.out}[/green]")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ds = ExcelEngine().load_sheet(args.file, sheet_name=args.sheet)
    engine = ValidationEngine()
    issues = engine.validate(ds)
    score = engine.quality_score(ds, issues)
    console.print(f"Quality score: [bold]{score}[/bold]  ({len(issues)} issues)")
    _print_df(engine.to_dataframe(issues), "Validation Issues", max_rows=30)
    if args.out:
        ExcelExporter().export_validation(issues, args.out)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    eng = ExcelEngine()
    files = eng.scan_folder(args.folder)
    all_ds: list[Dataset] = []
    for f in files:
        try:
            for s in eng.list_sheets(f):
                all_ds.append(eng.load_sheet(f, sheet_name=s, max_rows=args.limit))
        except Exception as e:
            console.print(f"[red]skip {f}: {e}[/red]")
    summary = AnalyticsEngine().summarise(all_ds)
    table = Table(title=f"Summary — {args.folder}")
    table.add_column("Metric"); table.add_column("Value", justify="right")
    for k, v in summary.__dict__.items():
        table.add_row(k, f"{v:,}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v))
    console.print(table)
    return 0


def cmd_export_report(args: argparse.Namespace) -> int:
    eng = ExcelEngine()
    files = eng.scan_folder(args.folder)
    all_ds: list[Dataset] = []
    for f in files:
        try:
            for s in eng.list_sheets(f):
                all_ds.append(eng.load_sheet(f, sheet_name=s, max_rows=args.limit))
        except Exception as e:
            console.print(f"[red]skip {f}: {e}[/red]")

    summary = AnalyticsEngine().summarise(all_ds)
    duplicates: list = []
    issues: list = []
    for ds in all_ds:
        duplicates.extend(DuplicateEngine().detect_smart(ds, threshold=args.threshold))
        issues.extend(ValidationEngine().validate(ds))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rg = ReportGenerator()
    rg.summary_json(summary, out / "summary.json")
    rg.summary_html(summary, duplicates, issues, out / "summary.html")
    rg.summary_pdf(summary, duplicates, out / "summary.pdf")
    ExcelExporter().export_duplicates(duplicates, out / "duplicates.xlsx")
    ExcelExporter().export_validation(issues, out / "validation.xlsx")
    console.print(f"[green]Report package written to {out}[/green]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("excelintel", description="ExcelIntel CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan"); s.add_argument("folder"); s.add_argument("--no-recursive", action="store_true"); s.set_defaults(func=cmd_scan)

    s = sub.add_parser("info"); s.add_argument("file"); s.add_argument("--sheet"); s.set_defaults(func=cmd_info)

    s = sub.add_parser("duplicates")
    s.add_argument("file"); s.add_argument("--sheet"); s.add_argument("--column")
    s.add_argument("--threshold", type=float, default=88.0)
    s.add_argument("--clean", action="store_true"); s.add_argument("--out")
    s.set_defaults(func=cmd_duplicates)

    s = sub.add_parser("merge")
    s.add_argument("left"); s.add_argument("right"); s.add_argument("--on", required=True)
    s.add_argument("--how", default="inner")
    s.add_argument("--left-sheet"); s.add_argument("--right-sheet"); s.add_argument("--out")
    s.set_defaults(func=cmd_merge)

    s = sub.add_parser("validate"); s.add_argument("file"); s.add_argument("--sheet")
    s.add_argument("--out"); s.set_defaults(func=cmd_validate)

    s = sub.add_parser("summary"); s.add_argument("folder"); s.add_argument("--limit", type=int)
    s.set_defaults(func=cmd_summary)

    s = sub.add_parser("export-report")
    s.add_argument("folder"); s.add_argument("--out", default="reports")
    s.add_argument("--threshold", type=float, default=88.0)
    s.add_argument("--limit", type=int); s.set_defaults(func=cmd_export_report)
    return p


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
