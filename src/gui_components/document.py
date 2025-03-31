"""
Document component for Document Version Control System.
Handles the document content viewing and editing.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

from .base import UIComponent

class DocumentComponent(UIComponent):
    """Document content editor component"""
    
    def __init__(self, parent, app_state):
        super().__init__(parent, app_state)
        
        # Register for events
        self.app_state.register_callback("document_loaded", self.update_document_view)
        self.app_state.register_callback("document_cleared", self.clear_document_view)
        self.app_state.register_callback("document_updated", self.refresh_document_view)
        
        self.create_ui()
    
    def create_ui(self):
        """Create the document editor UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Info bar
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Document:").pack(side=tk.LEFT, padx=5)
        self.doc_name_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.doc_name_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(info_frame, text="Version:").pack(side=tk.LEFT, padx=5)
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(info_frame, textvariable=self.version_var, width=5)
        self.version_combo.pack(side=tk.LEFT, padx=5)
        self.version_combo.bind("<<ComboboxSelected>>", self.on_version_change)
        
        # Document content text area
        self.content_text = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button bar
        btn_bar = ttk.Frame(self.frame)
        btn_bar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_bar, text="Update Document", 
                 command=self.update_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="Version History", 
                 command=self.view_history).pack(side=tk.LEFT, padx=5)
    
    def update_document_view(self, doc_id, metadata, content, **kwargs):
        """Update the document view with loaded document"""
        # Update UI
        self.doc_name_var.set(f"{metadata['name']} ({metadata['type']})")
        
        # Update version dropdown
        versions = [str(v["version"]) for v in metadata["versions"]]
        self.version_combo["values"] = versions
        self.version_var.set(str(metadata["current_version"]))
        
        # Update content
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
    
    def clear_document_view(self):
        """Clear the document view"""
        self.doc_name_var.set("")
        self.version_combo["values"] = []
        self.version_var.set("")
        self.content_text.delete(1.0, tk.END)
    
    def refresh_document_view(self, doc_id, content, new_version, **kwargs):
        """Refresh the document view after an update"""
        # Update version dropdown
        versions = self.version_combo["values"]
        if str(new_version) not in versions:
            versions = list(versions)
            versions.append(str(new_version))
            self.version_combo["values"] = versions
        
        self.version_var.set(str(new_version))
        
        # Update content
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
    
    def on_version_change(self, event):
        """Handle version selection from dropdown"""
        if not self.app_state.current_doc_id:
            return
        
        try:
            version = int(self.version_var.get())
            content, _ = self.app_state.doc_manager.get_document(
                self.app_state.current_doc_id, version
            )
            
            # Update content
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, content)
            
            # Notify for auto-refresh if needed
            self.app_state.notify("version_changed", version=version)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load version: {str(e)}")
    
    def update_document(self):
        """Update the current document"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        # Ask if user wants to update from file or current content
        choice_dialog = tk.Toplevel(self.parent)
        choice_dialog.title("Update Document")
        choice_dialog.geometry("400x150")
        choice_dialog.transient(self.parent)
        choice_dialog.grab_set()
        
        ttk.Label(choice_dialog, text="How would you like to update the document?").pack(pady=(20, 10))
        
        def update_from_file():
            choice_dialog.destroy()
            file_path = filedialog.askopenfilename(
                title="Select updated file",
                filetypes=(("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*"))
            )
            
            if not file_path:
                return
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self._complete_update(content)
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
        
        def update_from_content():
            choice_dialog.destroy()
            content = self.content_text.get(1.0, tk.END)
            self._complete_update(content)
        
        btn_frame = ttk.Frame(choice_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="From File", 
                  command=update_from_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="From Current Content", 
                  command=update_from_content).pack(side=tk.LEFT, padx=10)
        
        # Center dialog on parent window
        choice_dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - choice_dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - choice_dialog.winfo_height()) // 2
        choice_dialog.geometry(f"+{x}+{y}")
        
        choice_dialog.wait_window()
    
    def _complete_update(self, content):
        """Complete the document update process"""
        # Ask for change description
        desc_dialog = tk.Toplevel(self.parent)
        desc_dialog.title("Change Description")
        desc_dialog.geometry("400x200")
        desc_dialog.transient(self.parent)
        desc_dialog.grab_set()
        
        ttk.Label(desc_dialog, text="Enter a description of the changes:").pack(pady=(20, 5))
        
        desc_text = scrolledtext.ScrolledText(desc_dialog, height=5, width=40, wrap=tk.WORD)
        desc_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        def do_update():
            description = desc_text.get(1.0, tk.END).strip()
            if not description:
                description = f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                self.app_state.update_current_document(content, description)
                desc_dialog.destroy()
                messagebox.showinfo("Success", "Document updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update document: {str(e)}")
        
        ttk.Button(desc_dialog, text="Update", command=do_update).pack(pady=10)
        
        # Center dialog on parent window
        desc_dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - desc_dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - desc_dialog.winfo_height()) // 2
        desc_dialog.geometry(f"+{x}+{y}")
        
        desc_dialog.wait_window()
    
    def view_history(self):
        """View version history of the current document"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        try:
            versions = self.app_state.doc_manager.get_version_history(self.app_state.current_doc_id)
            
            # Create history dialog
            history_dialog = tk.Toplevel(self.parent)
            history_dialog.title(f"Version History: {self.app_state.current_doc_name}")
            history_dialog.geometry("500x400")
            history_dialog.transient(self.parent)
            
            # Create treeview for versions
            columns = ("Version", "Date", "Changes")
            tree = ttk.Treeview(history_dialog, columns=columns, show="headings")
            
            # Configure columns
            tree.heading("Version", text="Version")
            tree.heading("Date", text="Date")
            tree.heading("Changes", text="Changes")
            
            tree.column("Version", width=80, anchor="center")
            tree.column("Date", width=150)
            tree.column("Changes", width=250)
            
            # Add vertical scrollbar
            scrollbar = ttk.Scrollbar(history_dialog, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
            
            # Populate treeview
            for version in versions:
                # Extract date part from ISO timestamp
                date_str = version["timestamp"].split("T")[0]
                tree.insert("", tk.END, values=(
                    version["version"],
                    date_str,
                    version["changes"]
                ))
            
            # Add button frame
            button_frame = ttk.Frame(history_dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Function to compare selected versions
            def compare_selected():
                selection = tree.selection()
                if len(selection) != 2:
                    messagebox.showinfo("Info", "Please select exactly two versions to compare.")
                    return
                
                # Get version numbers from selected items
                versions = []
                for item_id in selection:
                    version = tree.item(item_id, "values")[0]
                    versions.append(version)
                
                # Notify to update diff view
                self.app_state.notify("compare_versions", v1=versions[0], v2=versions[1])
                
                # Close the dialog
                history_dialog.destroy()
            
            ttk.Button(button_frame, text="Compare Selected", 
                     command=compare_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", 
                     command=history_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Center dialog on parent window
            history_dialog.update_idletasks()
            x = self.parent.winfo_x() + (self.parent.winfo_width() - history_dialog.winfo_width()) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - history_dialog.winfo_height()) // 2
            history_dialog.geometry(f"+{x}+{y}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load version history: {str(e)}")