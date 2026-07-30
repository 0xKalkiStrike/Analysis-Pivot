"""ExcelIntel main application window."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QApplication, QDockWidget, QFileDialog,
                                QLabel, QMainWindow, QMessageBox, QProgressBar,
                                QStatusBar, QTabWidget, QToolBar, QWidget)

from .. import APP_NAME, APP_TAGLINE, __version__
from ..core.config import get_config
from ..core.logger import get_logger
from ..engine import AnalyticsEngine, ExcelEngine
from ..export import ExcelExporter, ReportGenerator
from ..models import Dataset
from ..services import FileWatcher, ProjectService, SavedView
from .theme import apply_theme
from .dialogs import Command, CommandPalette, DrillThroughDialog
from .widgets import (ChartViewWidget, DashboardWidget, DataViewerWidget,
                       DuplicateViewWidget, FileExplorerWidget,
                       MergeWizardDialog, PivotBuilderWidget,
                       RelationshipViewWidget, SavedViewsWidget,
                       SqlConsoleWidget, ValidationViewWidget)

log = get_logger(__name__)


class LoadWorker(QThread):
    finished_ok = Signal(list)   # list[Dataset]
    error = Signal(str)
    progress = Signal(int, int, str)  # done, total, current

    def __init__(self, paths: list[str], engine: ExcelEngine) -> None:
        super().__init__()
        self.paths = paths
        self.engine = engine

    def run(self) -> None:
        try:
            datasets: list[Dataset] = []
            total = 0
            expanded: list[tuple[str, str]] = []
            for p in self.paths:
                try:
                    for sh in self.engine.list_sheets(p):
                        expanded.append((p, sh))
                except Exception as e:
                    log.warning(f"skip {p}: {e}")
            total = len(expanded) or 1
            for i, (p, sh) in enumerate(expanded, 1):
                self.progress.emit(i - 1, total, f"{Path(p).name} · {sh}")
                try:
                    ds = self.engine.load_sheet(p, sheet_name=sh)
                    datasets.append(ds)
                except Exception as e:
                    log.error(f"load failed {p}::{sh}: {e}")
            self.progress.emit(total, total, "Done")
            self.finished_ok.emit(datasets)
        except Exception as e:  # pragma: no cover
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = get_config()
        self.setWindowTitle(f"{APP_NAME} — {APP_TAGLINE}")
        self.resize(1440, 900)
        self.setAcceptDrops(True)

        self.excel = ExcelEngine(max_workers=self.cfg.max_workers)
        self.datasets: dict[str, Dataset] = {}
        self.project_service = ProjectService()
        self.current_project = self.project_service.new("Untitled")
        self.saved_views_list: list[SavedView] = []
        self.watcher = FileWatcher(parent=self)
        self.watcher.file_changed.connect(self._on_file_changed)
        self.live_refresh_enabled = True

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        # Central: tab widget
        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setMovable(True)
        self.setCentralWidget(self.tabs)

        self.dashboard = DashboardWidget()
        self.data_viewer = DataViewerWidget()
        self.duplicates = DuplicateViewWidget()
        self.validation = ValidationViewWidget()
        self.sql = SqlConsoleWidget()
        self.pivot = PivotBuilderWidget()
        self.relationships = RelationshipViewWidget()
        self.charts = ChartViewWidget(title="Column Explorer")

        self.tabs.addTab(self.dashboard, "📊  Dashboard")
        self.tabs.addTab(self.data_viewer, "📄  Data")
        self.tabs.addTab(self.duplicates, "🧬  Duplicates")
        self.tabs.addTab(self.validation, "✅  Validation")
        self.tabs.addTab(self.pivot, "🔀  Pivot")
        self.tabs.addTab(self.relationships, "🔗  Relationships")
        self.tabs.addTab(self.sql, "⌨️  SQL")
        self.tabs.addTab(self.charts, "📈  Charts")
        self.tab_names = {
            0: "dashboard", 1: "data", 2: "duplicates", 3: "validation",
            4: "pivot", 5: "relationships", 6: "sql", 7: "charts",
        }

        self.duplicates.export_requested.connect(self._export_duplicates)
        self.validation.export_requested.connect(self._export_validation)

        # Cross-filter wiring from Dashboard
        self.dashboard.dataset_selected.connect(self._cross_filter_dataset)
        self.dashboard.quality_selected.connect(self._cross_filter_quality)
        self.dashboard.top_value_selected.connect(self._cross_filter_top_value)

        # Drill-through wiring from Pivot
        self.pivot.drill_through_requested.connect(self._show_drill_through)

        # Left dock: file explorer
        self.explorer = FileExplorerWidget()
        self.explorer.open_files_requested.connect(self.open_paths)
        self.explorer.open_folder_requested.connect(self.open_folder)
        self.explorer.file_activated.connect(self._on_dataset_activated)
        dock = QDockWidget("Data Sources", self)
        dock.setWidget(self.explorer)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock.setMinimumWidth(280)

        # Right dock: saved views
        self.saved_views = SavedViewsWidget()
        self.saved_views.save_current_requested.connect(self._save_current_view)
        self.saved_views.apply_view_requested.connect(self._apply_saved_view)
        self.saved_views.views_changed.connect(self._on_views_changed)
        dock_views = QDockWidget("Saved Views", self)
        dock_views.setWidget(self.saved_views)
        dock_views.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_views.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_views)
        dock_views.setMinimumWidth(240)

    def _build_menu(self) -> None:
        mb = self.menuBar()
        m_file = mb.addMenu("&File")
        m_file.addAction(self._act("Open Files…", self.explorer._on_open_files, "Ctrl+O"))
        m_file.addAction(self._act("Open Folder…", self.explorer._on_open_folder, "Ctrl+Shift+O"))
        m_file.addSeparator()
        m_file.addAction(self._act("Save Project…", self.save_project, "Ctrl+S"))
        m_file.addAction(self._act("Load Project…", self.load_project))
        m_file.addSeparator()
        m_file.addAction(self._act("Export Report…", self.export_full_report))
        m_file.addAction(self._act("Export Current Sheet…", self.export_current))
        m_file.addSeparator()
        m_file.addAction(self._act("Exit", self.close, "Ctrl+Q"))

        m_data = mb.addMenu("&Data")
        m_data.addAction(self._act("Merge Wizard…", self.open_merge_wizard, "Ctrl+M"))
        m_data.addAction(self._act("Discover Relationships", self.discover_relationships, "Ctrl+R"))
        m_data.addAction(self._act("Refresh Dashboard", self.refresh_dashboard, "F5"))
        m_data.addSeparator()
        self.act_live_refresh = QAction("Live Refresh (watch files)", self, checkable=True)
        self.act_live_refresh.setChecked(True)
        self.act_live_refresh.toggled.connect(self._toggle_live_refresh)
        m_data.addAction(self.act_live_refresh)

        m_view = mb.addMenu("&View")
        m_view.addAction(self._act("Toggle Theme", self.toggle_theme))
        m_view.addAction(self._act("Save Current View…", lambda: self.saved_views._on_save(), "Ctrl+B"))
        m_view.addAction(self._act("Command Palette…", self.open_command_palette, "Ctrl+P"))

        m_help = mb.addMenu("&Help")
        m_help.addAction(self._act("About", self.show_about))

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False); tb.setIconSize(tb.iconSize())
        self.addToolBar(Qt.TopToolBarArea, tb)
        tb.addAction(self._act("Open", self.explorer._on_open_files))
        tb.addAction(self._act("Folder", self.explorer._on_open_folder))
        tb.addSeparator()
        tb.addAction(self._act("Merge", self.open_merge_wizard))
        tb.addAction(self._act("Refresh", self.refresh_dashboard))
        tb.addSeparator()
        tb.addAction(self._act("Report", self.export_full_report))
        tb.addAction(self._act("Theme", self.toggle_theme))
        from PySide6.QtWidgets import QSizePolicy
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        self.subtitle = QLabel("Ready"); self.subtitle.setStyleSheet("color:#8b8ba8; padding-right:12px;")
        tb.addWidget(self.subtitle)

    def _build_statusbar(self) -> None:
        sb = QStatusBar(); self.setStatusBar(sb)
        self.progress = QProgressBar(); self.progress.setMaximumWidth(240); self.progress.hide()
        self.status_label = QLabel(f"{APP_NAME} v{__version__}  ·  offline")
        sb.addPermanentWidget(self.status_label)
        sb.addPermanentWidget(self.progress)

    def _act(self, text: str, slot, shortcut: str | None = None) -> QAction:
        a = QAction(text, self); a.triggered.connect(slot)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        return a

    # ------------------------------------------------------------------ actions
    def open_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        self.subtitle.setText(f"Loading {len(paths)} file(s)…")
        self.progress.show(); self.progress.setRange(0, 100); self.progress.setValue(0)
        self.worker = LoadWorker(paths, self.excel)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_loaded)
        self.worker.error.connect(lambda e: QMessageBox.critical(self, "Load error", e))
        self.worker.start()

    def open_folder(self, folder: str) -> None:
        files = self.excel.scan_folder(folder)
        self.open_paths([str(f) for f in files])

    def _on_progress(self, done: int, total: int, current: str) -> None:
        pct = int(100 * done / max(total, 1))
        self.progress.setValue(pct)
        self.subtitle.setText(f"Loading… {current}   ({done}/{total})")

    def _on_loaded(self, datasets: list[Dataset]) -> None:
        for ds in datasets:
            key = ds.name
            self.datasets[key] = ds
            if ds.source:
                self.explorer.add_dataset(
                    ds.source.file_path, ds.source.sheet_name,
                    ds.rows, ds.cols, ds.source.file_size,
                )
        # Live refresh: watch every unique source file
        if self.live_refresh_enabled:
            paths = list({ds.source.file_path for ds in datasets if ds.source})
            self.watcher.add_paths(paths)

        self.subtitle.setText(f"Loaded {len(self.datasets)} dataset(s)  ·  watching {len(self.watcher.files())} file(s)")
        self.progress.hide()
        self.refresh_dashboard()
        self.pivot.set_datasets(self.datasets)
        self.relationships.set_datasets(self.datasets)
        if datasets:
            self._activate_dataset(datasets[0])

    def _on_dataset_activated(self, path: str, sheet: str) -> None:
        key = f"{Path(path).name} :: {sheet}"
        ds = self.datasets.get(key)
        if not ds:
            return
        self._activate_dataset(ds)

    def _activate_dataset(self, ds: Dataset) -> None:
        self.data_viewer.set_dataset(ds)
        self.duplicates.set_dataset(ds)
        self.validation.set_dataset(ds)
        self.sql.register_datasets(self.datasets)
        self.pivot.set_datasets(self.datasets, select=ds.name)
        self.relationships.set_datasets(self.datasets)
        self.dashboard.set_active_dataset(ds)
        self.tabs.setCurrentWidget(self.data_viewer)

    def refresh_dashboard(self) -> None:
        summary = AnalyticsEngine().summarise(list(self.datasets.values()))
        per_sheet = [(k[:24], v.rows) for k, v in self.datasets.items()][:12]
        self.dashboard.update_summary(summary, per_sheet)

    # ------------------------------------------------------------------ merge
    def open_merge_wizard(self) -> None:
        if len(self.datasets) < 2:
            QMessageBox.information(self, "Merge", "Load at least two datasets to merge.")
            return
        dlg = MergeWizardDialog(self.datasets, self)
        if dlg.exec() and dlg.result_obj is not None:
            merged = dlg.result_obj.dataset
            key = f"MERGED :: {merged.name}"
            self.datasets[key] = merged
            self.explorer.list.addItem(key)
            self._activate_dataset(merged)
            self.refresh_dashboard()

    # ------------------------------------------------------------------ export
    def export_current(self) -> None:
        df = self.data_viewer.current_dataframe()
        if df is None or df.is_empty():
            QMessageBox.information(self, "Export", "No dataset in current view."); return
        p, _ = QFileDialog.getSaveFileName(self, "Export sheet", "sheet.xlsx", "Excel (*.xlsx)")
        if not p: return
        from ..models import Dataset as DS
        ExcelExporter().export_dataset(DS(name=self.data_viewer.title.text(), df=df), p)
        QMessageBox.information(self, "Export complete", f"Written {p}")

    def _export_duplicates(self, groups) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Export duplicates", "duplicates.xlsx", "Excel (*.xlsx)")
        if not p: return
        ExcelExporter().export_duplicates(groups, p)
        QMessageBox.information(self, "Export", f"Written {p}")

    def _export_validation(self, issues) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Export validation", "validation.xlsx", "Excel (*.xlsx)")
        if not p: return
        ExcelExporter().export_validation(issues, p)
        QMessageBox.information(self, "Export", f"Written {p}")

    def export_full_report(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Report output folder")
        if not folder: return
        summary = AnalyticsEngine().summarise(list(self.datasets.values()))
        from ..engine import DuplicateEngine, ValidationEngine
        dups: list = []; issues: list = []
        for ds in self.datasets.values():
            dups.extend(DuplicateEngine().detect_smart(ds))
            issues.extend(ValidationEngine().validate(ds))
        rg = ReportGenerator()
        rg.summary_json(summary, Path(folder) / "summary.json")
        rg.summary_html(summary, dups, issues, Path(folder) / "summary.html")
        rg.summary_pdf(summary, dups, Path(folder) / "summary.pdf")
        ExcelExporter().export_duplicates(dups, Path(folder) / "duplicates.xlsx")
        ExcelExporter().export_validation(issues, Path(folder) / "validation.xlsx")
        QMessageBox.information(self, "Report complete", f"Written to {folder}")

    # ------------------------------------------------------------------ project
    def save_project(self) -> None:
        name, ok = self._prompt_text("Project name")
        if not ok or not name: return
        proj = self.project_service.new(name)
        proj.files = list({ds.source.file_path for ds in self.datasets.values() if ds.source})
        proj.sheets = [{"file": ds.source.file_path, "sheet": ds.source.sheet_name}
                       for ds in self.datasets.values() if ds.source]
        proj.settings = {"theme": self.cfg.theme, "similarity_threshold": self.cfg.similarity_threshold}
        proj.bookmarks = [v.to_dict() for v in self.saved_views_list]
        path = self.project_service.save(proj)
        self.current_project = proj
        self.setWindowTitle(f"{APP_NAME} — {proj.name}")
        QMessageBox.information(self, "Project saved", f"Written {path}")

    def load_project(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Load project", self.cfg.projects_dir, "ExcelIntel (*.eip)")
        if not p: return
        proj = self.project_service.load(p)
        self.current_project = proj
        self.setWindowTitle(f"{APP_NAME} — {proj.name}")
        # Restore saved views
        self.saved_views_list = [SavedView.from_dict(d) for d in proj.bookmarks or []]
        self.saved_views.set_views(self.saved_views_list)
        # Load referenced files
        paths = proj.files or [s["file"] for s in proj.sheets]
        self.open_paths(list(set(paths)))

    def _prompt_text(self, prompt: str) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, "ExcelIntel", prompt)

    # ------------------------------------------------------------------ misc
    def toggle_theme(self) -> None:
        self.cfg.theme = "light" if self.cfg.theme == "dark" else "dark"
        self.cfg.save()
        apply_theme(QApplication.instance(), self.cfg.theme)

    def show_about(self) -> None:
        QMessageBox.information(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{__version__}<br>{APP_TAGLINE}<br><br>"
            "Fully offline, Python-only enterprise BI platform.<br>"
            "© 2026 — MIT License",
        )

    # ------------------------------------------------------------------ relationships
    def discover_relationships(self) -> None:
        self.tabs.setCurrentWidget(self.relationships)
        self.relationships.set_datasets(self.datasets)
        self.relationships.scan()

    # ------------------------------------------------------------------ live refresh
    def _toggle_live_refresh(self, on: bool) -> None:
        self.live_refresh_enabled = on
        self.watcher.set_enabled(on)
        if not on:
            self.watcher.clear()
        else:
            paths = list({ds.source.file_path for ds in self.datasets.values() if ds.source})
            self.watcher.add_paths(paths)
        self.subtitle.setText(
            f"Live refresh {'on' if on else 'off'}  ·  watching {len(self.watcher.files())} file(s)"
        )

    def _on_file_changed(self, path: str) -> None:
        # Reload every sheet from this file that we currently have loaded.
        affected = [ds.source.sheet_name for ds in self.datasets.values()
                    if ds.source and ds.source.file_path == path]
        if not affected:
            return
        log.info(f"Reloading {len(affected)} sheet(s) from {path}")
        try:
            for sheet in affected:
                ds = self.excel.load_sheet(path, sheet_name=sheet)
                self.datasets[ds.name] = ds
        except Exception as e:
            log.error(f"Live reload failed for {path}: {e}")
            return
        self.refresh_dashboard()
        self.pivot.set_datasets(self.datasets)
        self.relationships.set_datasets(self.datasets)
        self.sql.register_datasets(self.datasets)
        current_ds = self.datasets.get(self.data_viewer.title.text())
        if current_ds:
            self.data_viewer.set_dataset(current_ds)
        self.subtitle.setText(f"Auto-refreshed: {Path(path).name}")

    # ------------------------------------------------------------------ saved views
    def _capture_current_view(self, name: str) -> SavedView:
        idx = self.tabs.currentIndex()
        tab_name = self.tab_names.get(idx, "dashboard")
        pivot_state = self.pivot.get_state()
        return SavedView(
            name=name,
            tab=tab_name,
            dataset=self.data_viewer.title.text() if self.data_viewer.title.text() != "No dataset loaded" else None,
            search_text=self.data_viewer.search.text(),
            search_column=self.data_viewer.column_combo.currentText(),
            duplicate_column=self.duplicates.column_combo.currentText(),
            duplicate_algo=self.duplicates.algo_combo.currentText(),
            duplicate_threshold=float(self.duplicates.threshold.value()),
            duplicate_clean=self.duplicates.chk_clean.isChecked(),
            pivot_rows=pivot_state["pivot_rows"],
            pivot_cols=pivot_state["pivot_cols"],
            pivot_value=pivot_state["pivot_value"],
            pivot_agg=pivot_state["pivot_agg"],
            sql_query=self.sql.editor.toPlainText(),
        )

    def _save_current_view(self, name: str) -> None:
        view = self._capture_current_view(name)
        self.saved_views_list = [v for v in self.saved_views_list if v.name != name] + [view]
        self.saved_views.add(view)
        self.subtitle.setText(f"Saved view '{name}'")

    def _apply_saved_view(self, view: SavedView) -> None:
        # Restore dataset if it exists
        if view.dataset and view.dataset in self.datasets:
            self._activate_dataset(self.datasets[view.dataset])
        # Data viewer search
        self.data_viewer.search.setText(view.search_text or "")
        if view.search_column and self.data_viewer.column_combo.findText(view.search_column) >= 0:
            self.data_viewer.column_combo.setCurrentText(view.search_column)
        # Duplicates
        if view.duplicate_column and self.duplicates.column_combo.findText(view.duplicate_column) >= 0:
            self.duplicates.column_combo.setCurrentText(view.duplicate_column)
        if view.duplicate_algo and self.duplicates.algo_combo.findText(view.duplicate_algo) >= 0:
            self.duplicates.algo_combo.setCurrentText(view.duplicate_algo)
        self.duplicates.threshold.setValue(view.duplicate_threshold)
        self.duplicates.chk_clean.setChecked(view.duplicate_clean)
        # Pivot
        self.pivot.apply_state({
            "pivot_rows": view.pivot_rows, "pivot_cols": view.pivot_cols,
            "pivot_value": view.pivot_value, "pivot_agg": view.pivot_agg,
        })
        # SQL
        if view.sql_query:
            self.sql.editor.setPlainText(view.sql_query)
        # Tab
        tab_map = {name: idx for idx, name in self.tab_names.items()}
        if view.tab in tab_map:
            self.tabs.setCurrentIndex(tab_map[view.tab])
        self.subtitle.setText(f"Applied view '{view.name}'")

    def _on_views_changed(self, views: list) -> None:
        self.saved_views_list = list(views)
        # Auto-persist to current project (if it has a name saved on disk)
        try:
            self.current_project.bookmarks = [v.to_dict() for v in self.saved_views_list]
            proj_path = self.project_service.path_for(self.current_project.name)
            if proj_path.exists():
                self.project_service.save(self.current_project, proj_path)
        except Exception as e:
            log.warning(f"Could not auto-save views: {e}")

    # ------------------------------------------------------------------ cross-filter
    def _cross_filter_dataset(self, full_name: str) -> None:
        ds = self.datasets.get(full_name)
        if ds:
            self._activate_dataset(ds)
            self.subtitle.setText(f"Filtered by dataset: {full_name}")

    def _cross_filter_quality(self, label: str) -> None:
        # Route quality-segment click to the relevant tab
        mapping = {
            "Duplicates": (self.duplicates, self.duplicates.run),
            "Missing": (self.validation, self.validation.run),
            "Unique": (self.data_viewer, None),
        }
        target = mapping.get(label)
        if not target:
            return
        widget, runner = target
        self.tabs.setCurrentWidget(widget)
        if runner:
            try:
                runner()
            except Exception as e:  # pragma: no cover
                log.warning(f"cross-filter action failed: {e}")
        self.subtitle.setText(f"Filtered by quality segment: {label}")

    def _cross_filter_top_value(self, column: str, value: str) -> None:
        # Apply as a search filter in the Data viewer
        if column and self.data_viewer.column_combo.findText(column) >= 0:
            self.data_viewer.column_combo.setCurrentText(column)
        self.data_viewer.search.setText(value)
        self.tabs.setCurrentWidget(self.data_viewer)
        self.subtitle.setText(f"Filtered where {column} = '{value}'")

    # ------------------------------------------------------------------ drill-through
    def _show_drill_through(self, payload: dict) -> None:
        dlg = DrillThroughDialog(
            dataset=payload["dataset"],
            row_filters=payload.get("row_filters", {}),
            column_filters=payload.get("column_filters", {}),
            value_column=payload.get("value_column"),
            aggregate=payload.get("aggregate", "sum"),
            parent=self,
        )
        dlg.exec()

    # ------------------------------------------------------------------ command palette
    def open_command_palette(self) -> None:
        if not hasattr(self, "_palette"):
            self._palette = CommandPalette(self)
        self._palette.set_commands(self._build_commands())
        self._palette.open()

    def _build_commands(self) -> list[Command]:
        cmds: list[Command] = []
        # Actions
        actions = [
            ("Open Files…", self.explorer._on_open_files, "Ctrl+O", "Load spreadsheets"),
            ("Open Folder…", self.explorer._on_open_folder, "Ctrl+Shift+O", "Scan a directory"),
            ("Save Project…", self.save_project, "Ctrl+S", "Persist workspace"),
            ("Load Project…", self.load_project, "", "Restore workspace"),
            ("Merge Wizard…", self.open_merge_wizard, "Ctrl+M", "Join two datasets"),
            ("Discover Relationships", self.discover_relationships, "Ctrl+R", "Auto FK inference"),
            ("Refresh Dashboard", self.refresh_dashboard, "F5", "Recompute KPIs"),
            ("Export Full Report…", self.export_full_report, "", "PDF + HTML + JSON + Excel"),
            ("Export Current Sheet…", self.export_current, "", "Export active data table"),
            ("Toggle Theme", self.toggle_theme, "", "Dark ↔ Light"),
            ("Toggle Live Refresh", lambda: self.act_live_refresh.toggle(), "", "Watch source files"),
            ("Save Current View…", lambda: self.saved_views._on_save(), "Ctrl+B", "Bookmark workspace state"),
        ]
        for label, action, sc, hint in actions:
            cmds.append(Command(label=label, action=action, category="Action", shortcut=sc, hint=hint))

        # Tabs
        tab_defs = [
            ("Go to Dashboard", self.dashboard),
            ("Go to Data", self.data_viewer),
            ("Go to Duplicates", self.duplicates),
            ("Go to Validation", self.validation),
            ("Go to Pivot", self.pivot),
            ("Go to Relationships", self.relationships),
            ("Go to SQL", self.sql),
            ("Go to Charts", self.charts),
        ]
        for label, widget in tab_defs:
            cmds.append(Command(
                label=label,
                action=lambda w=widget: self.tabs.setCurrentWidget(w),
                category="Navigate",
            ))

        # Datasets
        for name, ds in self.datasets.items():
            cmds.append(Command(
                label=f"Activate: {name}",
                action=lambda d=ds: self._activate_dataset(d),
                category="Dataset",
                hint=f"{ds.rows:,} rows × {ds.cols} cols",
            ))

        # Saved views
        for view in self.saved_views_list:
            cmds.append(Command(
                label=f"View: {view.name}",
                action=lambda v=view: self._apply_saved_view(v),
                category="View",
                hint=f"tab={view.tab} · dataset={view.dataset or '-'}",
            ))
        return cmds

    # ------------------------------------------------------------------ drag&drop
    def dragEnterEvent(self, e) -> None:  # noqa: N802
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.open_paths(paths)
