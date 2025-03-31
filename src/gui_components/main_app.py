"""
Main Application for Document Version Control System.
Coordinates all components and handles the overall layout.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .base import AppState
from .explorer import ExplorerComponent
from .document import DocumentComponent
from .diff import DiffComponent
from .ai_analysis import AIAnalysisComponent
from .dialogs import AboutDialog

class MainApplication:
    """Main application class that coordinates all components"""
    
class MainApplication:
    """Main application class that coordinates all components"""
    
    def __init__(self, root):
        """Initialize the main application"""
        self.root = root
        self.root.title("Document Version Control System")
        self.root.geometry("1000x700")
        
        # Initialize application state
        self.app_state = AppState()
        
        # Create UI elements
        self.create_main_ui()  # Call this first to initialize components
        self.create_menu()     # Then create the menu
        
        # Load initial document list
        self.app_state.refresh_document_list()
    
    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Document", 
                             command=self.explorer_component.new_document)
        file_menu.add_command(label="Update Current Document", 
                             command=self.document_component.update_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Version menu
        version_menu = tk.Menu(menubar, tearoff=0)
        version_menu.add_command(label="View Version History", 
                               command=self.document_component.view_history)
        version_menu.add_command(label="Compare Versions", 
                               command=self.show_diff_tab)
        menubar.add_cascade(label="Versions", menu=version_menu)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        ai_menu.add_command(label="Summarize Document", 
                          command=self.ai_component.summarize_document)
        ai_menu.add_command(label="Suggest Improvements", 
                          command=self.ai_component.suggest_improvements)
        ai_menu.add_command(label="Analyze Changes", 
                          command=self.ai_component.analyze_changes)
        menubar.add_cascade(label="AI Analysis", menu=ai_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: AboutDialog.show_about(self.root))
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_ui(self):
        """Create the main UI elements"""
        # Main paned window for resizable sections
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Create the explorer component
        self.explorer_component = ExplorerComponent(self.main_paned, self.app_state)
        self.main_paned.add(self.explorer_component.get_frame(), weight=1)
        
        # Right panel with notebook for content and diff views
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=4)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create document component
        self.document_component = DocumentComponent(self.notebook, self.app_state)
        self.notebook.add(self.document_component.get_frame(), text="Document")
        
        # Create diff component
        self.diff_component = DiffComponent(self.notebook, self.app_state)
        self.notebook.add(self.diff_component.get_frame(), text="Compare")
        
        # Create AI analysis component
        self.ai_component = AIAnalysisComponent(self.notebook, self.app_state)
        self.notebook.add(self.ai_component.get_frame(), text="AI Analysis")
        
        # Register notebook tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """Handle notebook tab changes"""
        current_tab = self.notebook.index(self.notebook.select())
        # You can add specific behavior for tab changes here
    
    def show_diff_tab(self):
        """Switch to the diff tab and prepare for comparison"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        # Switch to diff tab
        self.notebook.select(1)  # Index 1 is the diff tab
        
        # If there are at least 2 versions, set up for comparison
        try:
            versions = self.app_state.doc_manager.get_version_history(self.app_state.current_doc_id)
            if len(versions) < 2:
                messagebox.showinfo("Info", "Need at least 2 versions to compare.")
                return
                
            # Update diff view
            self.diff_component.update_diff_view()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set up comparison: {str(e)}")