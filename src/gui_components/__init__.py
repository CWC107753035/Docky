"""
GUI Components package for Document Version Control System.
Exports the main application and component classes.
"""

# Import components
from .base import UIComponent, AppState
from .explorer import ExplorerComponent
from .document import DocumentComponent
from .diff import DiffComponent
from .ai_analysis import AIAnalysisComponent
from .dialogs import AboutDialog

# Import main application
from .main_app import MainApplication

# Export main classes
__all__ = [
    'UIComponent',
    'AppState',
    'ExplorerComponent',
    'DocumentComponent',
    'DiffComponent',
    'AIAnalysisComponent',
    'AboutDialog',
    'MainApplication'
]