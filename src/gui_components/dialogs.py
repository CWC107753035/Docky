"""
Dialog components for Document Version Control System.
Contains reusable dialog implementations.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

class AboutDialog:
    """About dialog implementation"""
    
    @staticmethod
    def show_about(parent):
        """Show the about dialog"""
        about_dialog = tk.Toplevel(parent)
        about_dialog.title("About Document Version Control")
        about_dialog.geometry("400x300")
        about_dialog.transient(parent)
        
        # Content
        ttk.Label(
            about_dialog, 
            text="Document Version Control System",
            font=("Arial", 14, "bold")
        ).pack(pady=(20, 5))
        
        ttk.Label(
            about_dialog,
            text="A simple document versioning system with diff capabilities."
        ).pack(pady=5)
        
        ttk.Label(
            about_dialog,
            text="Created for demonstration purposes."
        ).pack(pady=5)
        
        ttk.Label(
            about_dialog,
            text=f"Version 1.1 • {datetime.now().year}"
        ).pack(pady=10)
        
        # Close button
        ttk.Button(about_dialog, text="Close", command=about_dialog.destroy).pack(pady=20)
        
        # Center dialog on parent window
        about_dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - about_dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - about_dialog.winfo_height()) // 2
        about_dialog.geometry(f"+{x}+{y}")