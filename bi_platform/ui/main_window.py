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
from ..services import ProjectService
from .theme import apply_theme
from .widgets import (ChartViewWidget, DashboardWidget, DataViewerWidget,
                       DuplicateViewWidget, FileExplorerWidget,
                       MergeWizardDialog, SqlConsoleWidget,
                       ValidationViewWidget)

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
        self.charts = ChartViewWidget(title="Column Explorer")

        self.tabs.addTab(self.dashboard, "📊  Dashboard")
        self.tabs.addTab(self.data_viewer, "📄  Data")
        self.tabs.addTab(self.duplicates, "🧬  Duplicates")
        self.tabs.addTab(self.validation, "✅  Validation")
        self.tabs.addTab(self.sql, "⌨️  SQL")
        self.tabs.addTab(self.charts, "📈  Charts")

        self.duplicates.export_requested.connect(self._export_duplicates)
        self.validation.export_requested.connect(self._export_validation)

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
        m_data.addAction(self._act("Refresh Dashboard", self.refresh_dashboard, "F5"))

        m_view = mb.addMenu("&View")
        m_view.addAction(self._act("Toggle Theme", self.toggle_theme))

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
        self.subtitle.setText(f"Loaded {len(self.datasets)} dataset(s)")
        self.progress.hide()
        self.refresh_dashboard()
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
        path = self.project_service.save(proj)
        QMessageBox.information(self, "Project saved", f"Written {path}")

    def load_project(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Load project", self.cfg.projects_dir, "ExcelIntel (*.eip)")
        if not p: return
        proj = self.project_service.load(p)
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

    # ------------------------------------------------------------------ drag&drop
    def dragEnterEvent(self, e) -> None:  # noqa: N802
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.open_paths(paths)
