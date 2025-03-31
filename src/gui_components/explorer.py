"""
Explorer component for Document Version Control System.
Handles the document list and document operations.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .base import UIComponent

class ExplorerComponent(UIComponent):
    """Document explorer component"""
    
    def __init__(self, parent, app_state):
        super().__init__(parent, app_state)
        
        # Register for events
        self.app_state.register_callback("document_list_updated", self.update_document_list)
        self.app_state.register_callback("document_loaded", self.highlight_current_document)
        
        self.create_ui()
    
    def create_ui(self):
        """Create the document explorer UI"""
        self.frame = ttk.LabelFrame(self.parent, text="Explorer")
        
        # Document list with scrollbar
        self.inner_frame = ttk.Frame(self.frame)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Explorer toolbar
        explorer_toolbar = ttk.Frame(self.inner_frame)
        explorer_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(explorer_toolbar, text="New", command=self.new_document).pack(side=tk.LEFT, padx=2)
        ttk.Button(explorer_toolbar, text="Refresh", 
                 command=self.app_state.refresh_document_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(explorer_toolbar, text="Delete", command=self.delete_document).pack(side=tk.LEFT, padx=2)
        
        # Document listbox with scrollbar
        list_frame = ttk.Frame(self.inner_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.doc_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.doc_listbox.yview)
        self.doc_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.doc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.doc_listbox.bind('<<ListboxSelect>>', self.on_doc_select)
    
    def update_document_list(self, documents):
        """Update the document list display"""
        self.doc_listbox.delete(0, tk.END)
        
        for doc_id, doc in documents.items():
            self.doc_listbox.insert(tk.END, f"{doc['name']} (v{doc['current_version']})")
    
    def highlight_current_document(self, doc_id, **kwargs):
        """Highlight the current document in the list"""
        if not doc_id:
            return
            
        for i, item_id in enumerate(self.app_state.documents.keys()):
            if item_id == doc_id:
                self.doc_listbox.selection_clear(0, tk.END)
                self.doc_listbox.selection_set(i)
                self.doc_listbox.see(i)
                break
    
    def on_doc_select(self, event):
        """Handle document selection from the list"""
        selection = self.doc_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.app_state.documents):
            return
        
        doc_id = list(self.app_state.documents.keys())[index]
        self.app_state.set_current_document(doc_id)
    
    def new_document(self):
        """Create a new document"""
        file_path = filedialog.askopenfilename(
            title="Select file",
            filetypes=(("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*"))
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get document name from dialog
            name_dialog = tk.Toplevel(self.parent)
            name_dialog.title("New Document")
            name_dialog.geometry("400x200")
            name_dialog.transient(self.parent)
            name_dialog.grab_set()
            
            ttk.Label(name_dialog, text="Document Name:").pack(pady=(20, 5))
            name_var = tk.StringVar(value=os.path.basename(file_path))
            name_entry = ttk.Entry(name_dialog, textvariable=name_var, width=40)
            name_entry.pack(pady=5)
            
            ttk.Label(name_dialog, text="Document Type:").pack(pady=(10, 5))
            type_var = tk.StringVar(value=os.path.splitext(file_path)[1][1:] or "txt")
            type_entry = ttk.Entry(name_dialog, textvariable=type_var, width=10)
            type_entry.pack(pady=5)
            
            def create_doc():
                name = name_var.get()
                doc_type = type_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Document name cannot be empty.")
                    return
                
                try:
                    doc_id = self.app_state.doc_manager.create_document(content, name, doc_type)
                    messagebox.showinfo("Success", f"Document created with ID: {doc_id}")
                    name_dialog.destroy()
                    self.app_state.refresh_document_list()
                    self.app_state.set_current_document(doc_id)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create document: {str(e)}")
            
            ttk.Button(name_dialog, text="Create", command=create_doc).pack(pady=20)
            
            # Center dialog on parent window
            name_dialog.update_idletasks()
            x = self.parent.winfo_x() + (self.parent.winfo_width() - name_dialog.winfo_width()) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - name_dialog.winfo_height()) // 2
            name_dialog.geometry(f"+{x}+{y}")
            
            name_dialog.wait_window()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def delete_document(self):
        """Delete the selected document"""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a document to delete.")
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.app_state.documents):
            return
        
        doc_id = list(self.app_state.documents.keys())[index]
        doc_name = self.app_state.documents[doc_id]["name"]
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete '{doc_name}'?\nThis cannot be undone."):
            return
        
        try:
            self.app_state.doc_manager.delete_document(doc_id)
            messagebox.showinfo("Success", "Document deleted successfully.")
            
            # Clear if current document was deleted
            if self.app_state.current_doc_id == doc_id:
                self.app_state.set_current_document(None)
            
            self.app_state.refresh_document_list()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete document: {str(e)}")