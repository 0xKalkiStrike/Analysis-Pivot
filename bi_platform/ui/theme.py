"""Modern dark + light Qt stylesheets."""
from __future__ import annotations

DARK_QSS = """
* { font-family: 'Inter', 'Segoe UI', 'SF Pro Display', system-ui, sans-serif; }
QWidget { background-color: #0f0f14; color: #e6e6f0; font-size: 13px; }
QMainWindow, QDialog { background-color: #0f0f14; }
QMenuBar { background-color: #14141f; color: #d0d0e0; border-bottom: 1px solid #26263a; }
QMenuBar::item:selected { background-color: #2b2b45; }
QMenu { background-color: #16162a; color: #d0d0e0; border: 1px solid #2b2b45; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 6px; }
QMenu::item:selected { background-color: #3a2f8a; color: white; }

QToolBar { background-color: #14141f; border: none; padding: 6px; spacing: 4px; }
QToolButton { background-color: transparent; padding: 8px 12px; border-radius: 8px; color:#d0d0e0; }
QToolButton:hover { background-color: #22223a; color: #ffffff; }
QToolButton:checked { background-color: #3a2f8a; color: white; }
QToolButton:pressed { background-color: #4b3fbf; }

QPushButton {
  background-color: #5b4be0; color: white; border: none;
  padding: 8px 18px; border-radius: 10px; font-weight: 600;
}
QPushButton:hover { background-color: #6a5cf0; }
QPushButton:pressed { background-color: #4a3ed0; }
QPushButton:disabled { background-color: #2a2a3a; color: #6a6a80; }
QPushButton[flat="true"] {
  background-color: transparent; color:#c9b6ff; border:1px solid #2b2b45;
}
QPushButton[flat="true"]:hover { background-color: #1c1c2c; }

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
  background-color: #191925; border: 1px solid #2b2b45; border-radius: 8px;
  padding: 6px 10px; color: #e6e6f0; selection-background-color: #5b4be0;
}
QLineEdit:focus, QComboBox:focus { border-color: #7c5cff; }

QTableView, QTreeView, QListView {
  background-color: #12121c; border: 1px solid #2b2b45; border-radius: 8px;
  gridline-color: #26263a; alternate-background-color: #14142a;
  selection-background-color: #3a2f8a; selection-color: #ffffff;
}
QHeaderView::section {
  background-color: #1a1a2e; color: #c9b6ff; padding: 8px 12px;
  border: none; border-right: 1px solid #26263a; border-bottom: 1px solid #26263a;
  font-weight: 600;
}
QTableView::item { padding: 6px; }

QTabWidget::pane { border: 1px solid #2b2b45; border-radius: 10px; top: -1px; background-color: #12121c; }
QTabBar::tab {
  background-color: transparent; color: #8b8ba8; padding: 10px 18px;
  border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px;
}
QTabBar::tab:selected { background-color: #12121c; color: #ffffff; border: 1px solid #2b2b45; border-bottom: none; }
QTabBar::tab:hover:!selected { color: #d0d0e0; }

QDockWidget { titlebar-close-icon: url(none); }
QDockWidget::title { background-color: #14141f; padding: 8px 12px; color: #c9b6ff; font-weight: 600; }

QScrollBar:vertical { background: transparent; width: 12px; margin: 4px; }
QScrollBar::handle:vertical { background: #33334a; min-height: 40px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background: #4b4b6a; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 4px; }
QScrollBar::handle:horizontal { background: #33334a; min-width: 40px; border-radius: 6px; }

QStatusBar { background-color: #14141f; color: #8b8ba8; border-top: 1px solid #26263a; }
QProgressBar {
  background-color: #191925; border: 1px solid #2b2b45; border-radius: 8px;
  text-align: center; color: #ffffff; padding: 2px;
}
QProgressBar::chunk { background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5b4be0, stop:1 #b06bff); border-radius: 6px; }

QGroupBox { border: 1px solid #2b2b45; border-radius: 10px; margin-top: 14px; padding-top: 18px; color:#c9b6ff; font-weight:600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }

QLabel[kpi="true"] {
  background-color: #171727; border: 1px solid #2b2b45; border-radius: 12px;
  padding: 16px; color:#e6e6f0;
}
QLabel[kpi-label="true"] { color:#8b8ba8; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }
QLabel[kpi-value="true"] { color:#ffffff; font-size: 28px; font-weight: 700; }
QLabel[accent="true"] { color: #c9b6ff; }
"""

LIGHT_QSS = """
* { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
QWidget { background-color: #f7f7fb; color: #1a1a2e; font-size: 13px; }
QMainWindow, QDialog { background-color: #ffffff; }
QMenuBar { background-color: #ffffff; color: #1a1a2e; border-bottom: 1px solid #e2e2ee; }
QMenuBar::item:selected { background-color: #ece8ff; }
QMenu { background-color: #ffffff; color: #1a1a2e; border: 1px solid #e2e2ee; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 6px; }
QMenu::item:selected { background-color: #5b4be0; color: white; }
QToolBar { background-color: #ffffff; border: none; padding: 6px; spacing: 4px; border-bottom:1px solid #e2e2ee; }
QToolButton { background-color: transparent; padding: 8px 12px; border-radius: 8px; color:#1a1a2e; }
QToolButton:hover { background-color: #ece8ff; }
QToolButton:checked { background-color: #5b4be0; color: white; }
QPushButton {
  background-color: #5b4be0; color: white; border: none;
  padding: 8px 18px; border-radius: 10px; font-weight: 600;
}
QPushButton:hover { background-color: #6a5cf0; }
QPushButton[flat="true"] { background-color:#f0eeff; color:#5b4be0; border:1px solid #e2e2ee; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
  background-color: #ffffff; border: 1px solid #d4d4e2; border-radius: 8px;
  padding: 6px 10px; color: #1a1a2e;
}
QTableView { background-color: #ffffff; border: 1px solid #e2e2ee; border-radius: 8px; gridline-color: #eee; alternate-background-color:#faf9ff; }
QHeaderView::section { background-color: #f0eeff; color: #5b4be0; padding: 8px 12px; border: none; border-right:1px solid #e2e2ee; border-bottom:1px solid #e2e2ee; font-weight:600; }
QTabWidget::pane { border: 1px solid #e2e2ee; border-radius: 10px; top: -1px; background-color: #ffffff; }
QTabBar::tab { background-color: transparent; color: #8b8ba8; padding: 10px 18px; }
QTabBar::tab:selected { background-color: #ffffff; color: #5b4be0; border: 1px solid #e2e2ee; border-bottom: none; }
QStatusBar { background-color: #ffffff; color: #8b8ba8; border-top: 1px solid #e2e2ee; }
QLabel[kpi="true"] { background-color:#ffffff; border:1px solid #e2e2ee; border-radius:12px; padding:16px; }
QLabel[kpi-label="true"] { color:#8b8ba8; text-transform:uppercase; font-size:11px; letter-spacing:1px; }
QLabel[kpi-value="true"] { color:#1a1a2e; font-size:28px; font-weight:700; }
"""


def apply_theme(app, theme: str = "dark") -> None:
    app.setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)
