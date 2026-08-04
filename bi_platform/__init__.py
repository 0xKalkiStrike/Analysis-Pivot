APP_NAME = "ExcelIntel"
APP_TAGLINE = "Enterprise Excel Analytics & Business Intelligence Platform"
__version__ = "1.0.0"

from .ui.theme import DARK_QSS, LIGHT_QSS, apply_theme

__all__ = ["APP_NAME", "APP_TAGLINE", "__version__", "DARK_QSS", "LIGHT_QSS", "apply_theme"]
