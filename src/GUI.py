#!/usr/bin/env python3
"""
Improved GUI for Document Version Control System

This provides a graphical interface for the document versioning system
with a resizable document browser and integrated side-by-side diff view.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import webbrowser
from datetime import datetime
from document_manager import DocumentManager
from version_controller import VersionController

class DocumentVersioningGUI:
    """GUI for document versioning system."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Document Version Control System")
        self.root.geometry("1000x700")
        
        # Initialize document manager and version controller
        self.doc_manager = DocumentManager("my_documents")
        self.version_controller = VersionController(self.doc_manager)
        
        # Create directory if it doesn't exist
        os.makedirs("my_documents", exist_ok=True)
        
        # Current document tracking
        self.current_doc_id = None
        self.current_doc_name = None
        
        # Edit mode tracking for comparison view
        self.diff_edit_mode = False
        
        # Create UI elements
        self.create_menu()
        self.create_main_ui()
        
        # Load initial document list
        self.refresh_document_list()
    
    def create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Document", command=self.new_document)
        file_menu.add_command(label="Open Document", command=self.open_document)
        file_menu.add_command(label="Update Current Document", command=self.update_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Version menu
        version_menu = tk.Menu(menubar, tearoff=0)
        version_menu.add_command(label="View Version History", command=self.view_history)
        version_menu.add_command(label="Compare Versions", command=self.compare_versions)
        menubar.add_cascade(label="Versions", menu=version_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_ui(self):
        """Create the main UI elements."""
        # Main paned window for resizable sections
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Document explorer (resizable)
        self.explorer_frame = ttk.LabelFrame(self.main_paned, text="Explorer")
        
        # Document list with scrollbar
        self.explorer_inner_frame = ttk.Frame(self.explorer_frame)
        self.explorer_inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Explorer toolbar
        explorer_toolbar = ttk.Frame(self.explorer_inner_frame)
        explorer_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(explorer_toolbar, text="New", command=self.new_document).pack(side=tk.LEFT, padx=2)
        ttk.Button(explorer_toolbar, text="Refresh", command=self.refresh_document_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(explorer_toolbar, text="Delete", command=self.delete_document).pack(side=tk.LEFT, padx=2)
        
        # Document listbox with scrollbar in a frame
        list_frame = ttk.Frame(self.explorer_inner_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.doc_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.doc_listbox.yview)
        self.doc_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.doc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.doc_listbox.bind('<<ListboxSelect>>', self.on_doc_select)
        
        # Add explorer to the paned window
        self.main_paned.add(self.explorer_frame, weight=1)
        
        # Right panel with notebook for content and diff views
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=4)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Document content tab
        self.content_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.content_frame, text="Document")
        
        # Diff view tab
        self.diff_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.diff_frame, text="Compare")
        
        # Set up the content frame
        self.setup_content_frame()
        
        # Set up the diff frame
        self.setup_diff_frame()
    
    def setup_content_frame(self):
        """Set up the document content view."""
        # Info bar
        info_frame = ttk.Frame(self.content_frame)
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
        self.content_text = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button bar
        btn_bar = ttk.Frame(self.content_frame)
        btn_bar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_bar, text="Update Document", command=self.update_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="Compare Versions", command=self.compare_versions).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="Version History", command=self.view_history).pack(side=tk.LEFT, padx=5)
    
    def setup_diff_frame(self):
        """Set up the side-by-side diff view."""
        # Controls frame
        controls_frame = ttk.Frame(self.diff_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Version selection
        ttk.Label(controls_frame, text="Compare:").pack(side=tk.LEFT, padx=5)
        
        self.diff_v1_var = tk.StringVar()
        self.diff_v2_var = tk.StringVar()
        
        self.diff_v1_combo = ttk.Combobox(controls_frame, textvariable=self.diff_v1_var, width=5)
        ttk.Label(controls_frame, text="vs").pack(side=tk.LEFT, padx=5)
        self.diff_v2_combo = ttk.Combobox(controls_frame, textvariable=self.diff_v2_var, width=5)
        
        self.diff_v1_combo.pack(side=tk.LEFT, padx=5)
        self.diff_v2_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Compare", command=self.update_diff_view).pack(side=tk.LEFT, padx=10)
        
        # Add edit mode toggle button
        self.edit_mode_var = tk.StringVar(value="Enable Edit Mode")
        self.edit_mode_btn = ttk.Button(controls_frame, textvariable=self.edit_mode_var, command=self.toggle_diff_edit_mode)
        self.edit_mode_btn.pack(side=tk.LEFT, padx=10)
        
        # Add save edited version button (initially disabled)
        self.save_edit_btn = ttk.Button(controls_frame, text="Save Edited Version", command=self.save_edited_version, state=tk.DISABLED)
        self.save_edit_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(controls_frame, text="Auto-Refresh", command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=10)
        
        # Auto-refresh status
        self.auto_refresh = False
        self.auto_refresh_var = tk.StringVar(value="Auto-Refresh: Off")
        ttk.Label(controls_frame, textvariable=self.auto_refresh_var).pack(side=tk.LEFT, padx=10)
        
        # Create side-by-side frames for comparison
        self.side_by_side_frame = ttk.Frame(self.diff_frame)
        self.side_by_side_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left version pane
        left_frame = ttk.LabelFrame(self.side_by_side_frame, text="Version 1")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        self.left_header_var = tk.StringVar(value="Version: -")
        ttk.Label(left_frame, textvariable=self.left_header_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.left_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD)
        self.left_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.left_text.config(state=tk.DISABLED)  # Start as read-only
        
        # Right version pane
        right_frame = ttk.LabelFrame(self.side_by_side_frame, text="Version 2")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        self.right_header_var = tk.StringVar(value="Version: -")
        ttk.Label(right_frame, textvariable=self.right_header_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.right_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        self.right_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.right_text.config(state=tk.DISABLED)  # Start as read-only
        
        # Configure tags for highlighting differences
        for text_widget in [self.left_text, self.right_text]:
            text_widget.tag_configure("addition", background="#e6ffed")
            text_widget.tag_configure("deletion", background="#ffeef0")
            text_widget.tag_configure("change", background="#ffefd7")
            
        # Sync scrolling between the two text widgets
        def sync_scroll(*args):
            self.right_text.yview_moveto(args[0])
        
        def on_left_scroll(*args):
            self.right_text.yview_moveto(self.left_text.yview()[0])
        
        def on_right_scroll(*args):
            self.left_text.yview_moveto(self.right_text.yview()[0])
        
        # Connect the two scrollbars for synchronized scrolling
        self.left_text.vbar = self.left_text.vbar  # Get scrollbar reference
        self.right_text.vbar = self.right_text.vbar
        
        self.left_text.bind("<MouseWheel>", on_left_scroll)
        self.right_text.bind("<MouseWheel>", on_right_scroll)
        self.left_text.bind("<Key-Up>", on_left_scroll)
        self.left_text.bind("<Key-Down>", on_left_scroll)
        self.right_text.bind("<Key-Up>", on_right_scroll)
        self.right_text.bind("<Key-Down>", on_right_scroll)
        
        # Add an edit status bar
        self.edit_status_var = tk.StringVar(value="")
        self.edit_status_label = ttk.Label(self.diff_frame, textvariable=self.edit_status_var, foreground="blue")
        self.edit_status_label.pack(fill=tk.X, padx=5, pady=(0, 5), anchor=tk.W)
    
    def toggle_diff_edit_mode(self):
        """Toggle edit mode in the comparison view."""
        if not self.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        self.diff_edit_mode = not self.diff_edit_mode
        
        if self.diff_edit_mode:
            # Enable editing mode
            self.edit_mode_var.set("Disable Edit Mode")
            self.left_text.config(state=tk.NORMAL)
            self.right_text.config(state=tk.NORMAL)
            self.save_edit_btn.config(state=tk.NORMAL)
            self.edit_status_var.set("Edit mode is ON - Make changes directly in either version")
            
            # Change background color to indicate editable
            self.left_text.configure(background="#fffff0")  # Light cream
            self.right_text.configure(background="#fffff0")  # Light cream
        else:
            # Disable editing mode
            self.edit_mode_var.set("Enable Edit Mode")
            self.left_text.config(state=tk.DISABLED)
            self.right_text.config(state=tk.DISABLED)
            self.save_edit_btn.config(state=tk.DISABLED)
            self.edit_status_var.set("")
            
            # Restore default background
            self.left_text.configure(background="white")
            self.right_text.configure(background="white")
            
            # Refresh the view to restore highlights
            self.update_diff_view()
    
    def save_edited_version(self):
        """Save either the left or right version as a new document version."""
        if not self.current_doc_id or not self.diff_edit_mode:
            return
        
        # Ask which version to save
        choice_dialog = tk.Toplevel(self.root)
        choice_dialog.title("Save Edited Version")
        choice_dialog.geometry("400x200")
        choice_dialog.transient(self.root)
        choice_dialog.grab_set()
        
        ttk.Label(choice_dialog, text="Which version would you like to save?", font=("Arial", 10, "bold")).pack(pady=(20, 10))
        
        # Get version labels for buttons
        v1_label = f"Left Version ({self.diff_v1_var.get()})"
        v2_label = f"Right Version ({self.diff_v2_var.get()})"
        
        def save_left():
            choice_dialog.destroy()
            self._save_version_with_description(self.left_text.get(1.0, tk.END))
        
        def save_right():
            choice_dialog.destroy()
            self._save_version_with_description(self.right_text.get(1.0, tk.END))
        
        def merge_versions():
            choice_dialog.destroy()
            # Open merge dialog
            self._open_merge_dialog()
        
        btn_frame = ttk.Frame(choice_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text=v1_label, command=save_left).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(btn_frame, text=v2_label, command=save_right).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Add merge option
        ttk.Label(choice_dialog, text="OR").pack(pady=5)
        ttk.Button(choice_dialog, text="Merge Both Versions", command=merge_versions).pack(pady=10)
        
        # Center dialog on parent window
        choice_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - choice_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - choice_dialog.winfo_height()) // 2
        choice_dialog.geometry(f"+{x}+{y}")
        
        choice_dialog.wait_window()
    
    def _open_merge_dialog(self):
        """Open a dialog to create a merged version from both text panes."""
        merge_dialog = tk.Toplevel(self.root)
        merge_dialog.title("Merge Versions")
        merge_dialog.geometry("700x500")
        merge_dialog.transient(self.root)
        merge_dialog.grab_set()
        
        ttk.Label(
            merge_dialog, 
            text="Edit the merged content below:",
            font=("Arial", 10, "bold")
        ).pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # Merged text content
        merged_text = scrolledtext.ScrolledText(merge_dialog, wrap=tk.WORD)
        merged_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Populate with combined content
        left_content = self.left_text.get(1.0, tk.END)
        right_content = self.right_text.get(1.0, tk.END)
        
        # For a simple merge, we'll start with the right content (usually newer version)
        # and add a header to indicate it's merged
        merged_text.insert(tk.END, f"*** MERGED VERSION ***\n\n")
        merged_text.insert(tk.END, right_content)
        
        def save_merge():
            content = merged_text.get(1.0, tk.END)
            merge_dialog.destroy()
            self._save_version_with_description(content, default_desc="Merged version")
        
        btn_frame = ttk.Frame(merge_dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save Merged Version", command=save_merge).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", command=merge_dialog.destroy).pack(side=tk.RIGHT)
        
        # Center dialog
        merge_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - merge_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - merge_dialog.winfo_height()) // 2
        merge_dialog.geometry(f"+{x}+{y}")
    
    def _save_version_with_description(self, content, default_desc="Edited in compare view"):
        """Save the content as a new version after getting a description."""
        # Ask for change description
        desc_dialog = tk.Toplevel(self.root)
        desc_dialog.title("Change Description")
        desc_dialog.geometry("400x200")
        desc_dialog.transient(self.root)
        desc_dialog.grab_set()
        
        ttk.Label(desc_dialog, text="Enter a description of the changes:").pack(pady=(20, 5))
        
        desc_text = scrolledtext.ScrolledText(desc_dialog, height=5, width=40, wrap=tk.WORD)
        desc_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        desc_text.insert(tk.END, default_desc)
        
        def do_update():
            description = desc_text.get(1.0, tk.END).strip()
            if not description:
                description = f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                new_version = self.doc_manager.update_document(self.current_doc_id, content, description)
                messagebox.showinfo("Success", f"Document updated to version {new_version}")
                desc_dialog.destroy()
                
                # Refresh everything
                self.refresh_document_list()
                self.load_document(self.current_doc_id)
                
                # Update the comparison view
                self.diff_v2_var.set(str(new_version))  # Set right side to new version
                self.update_diff_view()
                
                # Turn off edit mode
                if self.diff_edit_mode:
                    self.toggle_diff_edit_mode()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update document: {str(e)}")
        
        ttk.Button(desc_dialog, text="Save New Version", command=do_update).pack(pady=10)
        
        # Center dialog on parent window
        desc_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - desc_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - desc_dialog.winfo_height()) // 2
        desc_dialog.geometry(f"+{x}+{y}")
        
        desc_dialog.wait_window()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh for diff view."""
        self.auto_refresh = not self.auto_refresh
        self.auto_refresh_var.set(f"Auto-Refresh: {'On' if self.auto_refresh else 'Off'}")
        
        # If turning on, update the diff view immediately
        if self.auto_refresh:
            self.update_diff_view()
    
    def refresh_document_list(self):
        """Refresh the document list."""
        # Skip if the explorer is minimized
        if not hasattr(self, 'doc_listbox') or not self.doc_listbox.winfo_exists():
            return
            
        self.doc_listbox.delete(0, tk.END)
        
        try:
            documents = self.doc_manager.list_documents()
            self.documents = {doc["id"]: doc for doc in documents}
            
            for doc_id, doc in self.documents.items():
                self.doc_listbox.insert(tk.END, f"{doc['name']} (v{doc['current_version']})")
            
            # Clear the current document view if no documents
            if not documents:
                self.clear_document_view()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load documents: {str(e)}")
    
    def clear_document_view(self):
        """Clear the document view."""
        self.current_doc_id = None
        self.current_doc_name = None
        self.doc_name_var.set("")
        self.version_combo["values"] = []
        self.version_var.set("")
        self.content_text.delete(1.0, tk.END)
        
        # Clear diff combos
        self.diff_v1_combo["values"] = []
        self.diff_v2_combo["values"] = []
        self.diff_v1_var.set("")
        self.diff_v2_var.set("")
        
        # Reset diff view
        self.left_text.config(state=tk.NORMAL)
        self.right_text.config(state=tk.NORMAL)
        self.left_text.delete(1.0, tk.END)
        self.right_text.delete(1.0, tk.END)
        self.left_header_var.set("Version: -")
        self.right_header_var.set("Version: -")
        self.left_text.config(state=tk.DISABLED)
        self.right_text.config(state=tk.DISABLED)
        
        # Disable edit mode if active
        if self.diff_edit_mode:
            self.toggle_diff_edit_mode()
    
    def on_doc_select(self, event):
        """Handle document selection from the list."""
        selection = self.doc_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.documents):
            return
        
        doc_id = list(self.documents.keys())[index]
        self.load_document(doc_id)
    
    def load_document(self, doc_id):
        """Load a document and display it."""
        try:
            # Get document content and metadata
            content, metadata = self.doc_manager.get_document(doc_id)
            
            # Update current document tracking
            self.current_doc_id = doc_id
            self.current_doc_name = metadata["name"]
            
            # Update UI
            self.doc_name_var.set(f"{metadata['name']} ({metadata['type']})")
            
            # Update version dropdown
            versions = [str(v["version"]) for v in metadata["versions"]]
            self.version_combo["values"] = versions
            self.version_var.set(str(metadata["current_version"]))
            
            # Update content
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, content)
            
            # Update diff version combos
            self.diff_v1_combo["values"] = versions
            self.diff_v2_combo["values"] = versions
            
            # Set default values for diff
            if len(versions) >= 2:
                self.diff_v1_var.set(versions[0])
                self.diff_v2_var.set(versions[-1])
            elif len(versions) == 1:
                self.diff_v1_var.set(versions[0])
                self.diff_v2_var.set(versions[0])
            
            # If auto-refresh is on, update the diff view
            if self.auto_refresh and len(versions) >= 2:
                self.update_diff_view()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load document: {str(e)}")
    
    def on_version_change(self, event):
        """Handle version selection from dropdown."""
        if not self.current_doc_id:
            return
        
        try:
            version = int(self.version_var.get())
            content, _ = self.doc_manager.get_document(self.current_doc_id, version)
            
            # Update content
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, content)
            
            # If auto-refresh is on, update the diff view
            if self.auto_refresh:
                self.update_diff_view()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load version: {str(e)}")
    
    def update_diff_view(self):
        """Update the side-by-side diff view with the selected versions."""
        if not self.current_doc_id:
            return
        
        try:
            v1 = int(self.diff_v1_var.get())
            v2 = int(self.diff_v2_var.get())
            
            if v1 == v2:
                messagebox.showinfo("Info", "Please select different versions to compare.")
                return
            
            # Get content of both versions
            content1, _ = self.doc_manager.get_document(self.current_doc_id, v1)
            content2, _ = self.doc_manager.get_document(self.current_doc_id, v2)
            
            # Update headers
            self.left_header_var.set(f"Version: {v1}")
            self.right_header_var.set(f"Version: {v2}")
            
            # Set text widgets to normal for updating
            was_edit_mode = self.diff_edit_mode
            if not was_edit_mode:
                self.left_text.config(state=tk.NORMAL)
                self.right_text.config(state=tk.NORMAL)
            
            # Clear the text widgets
            self.left_text.delete(1.0, tk.END)
            self.right_text.delete(1.0, tk.END)
            
            # Display the content
            self.left_text.insert(tk.END, content1)
            self.right_text.insert(tk.END, content2)
            
            # Get the changes
            changes = self.doc_manager.compare_versions(self.current_doc_id, v1, v2)
            
            # Highlight the differences
            self.highlight_differences(changes, content1, content2)
            
            # Set back to disabled if not in edit mode
            if not was_edit_mode:
                self.left_text.config(state=tk.DISABLED)
                self.right_text.config(state=tk.DISABLED)
            
            # Switch to the diff tab
            self.notebook.select(self.diff_frame)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate diff: {str(e)}")
    
    def highlight_differences(self, changes, content1, content2):
        """Highlight the differences in the side-by-side view."""
        # Split content into lines
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Process each change
        for change in changes:
            for line in change['lines']:
                if line['type'] == 'added':
                    # Find this line in the right text (version 2)
                    try:
                        line_content = line['content']
                        line_index = lines2.index(line_content)
                        
                        # Calculate position in text widget
                        start_pos = f"{line_index + 1}.0"
                        end_pos = f"{line_index + 1}.end"
                        
                        # Highlight in right text
                        self.right_text.tag_add("addition", start_pos, end_pos)
                    except ValueError:
                        # Line not found, might be partial change
                        pass
                
                elif line['type'] == 'removed':
                    # Find this line in the left text (version 1)
                    try:
                        line_content = line['content']
                        line_index = lines1.index(line_content)
                        
                        # Calculate position in text widget
                        start_pos = f"{line_index + 1}.0"
                        end_pos = f"{line_index + 1}.end"
                        
                        # Highlight in left text
                        self.left_text.tag_add("deletion", start_pos, end_pos)
                    except ValueError:
                        # Line not found, might be partial change
                        pass
    
    def new_document(self):
        """Create a new document."""
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
            name_dialog = tk.Toplevel(self.root)
            name_dialog.title("New Document")
            name_dialog.geometry("400x200")
            name_dialog.transient(self.root)
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
                    doc_id = self.doc_manager.create_document(content, name, doc_type)
                    messagebox.showinfo("Success", f"Document created with ID: {doc_id}")
                    name_dialog.destroy()
                    self.refresh_document_list()
                    self.load_document(doc_id)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create document: {str(e)}")
            
            ttk.Button(name_dialog, text="Create", command=create_doc).pack(pady=20)
            
            # Center dialog on parent window
            name_dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - name_dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - name_dialog.winfo_height()) // 2
            name_dialog.geometry(f"+{x}+{y}")
            
            name_dialog.wait_window()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def open_document(self):
        """Open a document (same as selecting from list)."""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a document from the list.")
            return
        
        self.on_doc_select(None)
    
    def update_document(self):
        """Update the current document."""
        if not self.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        # Ask if user wants to update from file or current content
        choice_dialog = tk.Toplevel(self.root)
        choice_dialog.title("Update Document")
        choice_dialog.geometry("400x150")
        choice_dialog.transient(self.root)
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
        
        ttk.Button(btn_frame, text="From File", command=update_from_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="From Current Content", command=update_from_content).pack(side=tk.LEFT, padx=10)
        
        # Center dialog on parent window
        choice_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - choice_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - choice_dialog.winfo_height()) // 2
        choice_dialog.geometry(f"+{x}+{y}")
        
        choice_dialog.wait_window()
    
    def _complete_update(self, content):
        """Complete the document update process."""
        # Ask for change description
        desc_dialog = tk.Toplevel(self.root)
        desc_dialog.title("Change Description")
        desc_dialog.geometry("400x200")
        desc_dialog.transient(self.root)
        desc_dialog.grab_set()
        
        ttk.Label(desc_dialog, text="Enter a description of the changes:").pack(pady=(20, 5))
        
        desc_text = scrolledtext.ScrolledText(desc_dialog, height=5, width=40, wrap=tk.WORD)
        desc_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        def do_update():
            description = desc_text.get(1.0, tk.END).strip()
            if not description:
                description = f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                new_version = self.doc_manager.update_document(self.current_doc_id, content, description)
                messagebox.showinfo("Success", f"Document updated to version {new_version}")
                desc_dialog.destroy()
                self.refresh_document_list()
                self.load_document(self.current_doc_id)
                
                # If auto-refresh is on, update the diff view
                if self.auto_refresh:
                    # Set the right side to the new version
                    self.diff_v2_var.set(str(new_version))
                    self.update_diff_view()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update document: {str(e)}")
        
        ttk.Button(desc_dialog, text="Update", command=do_update).pack(pady=10)
        
        # Center dialog on parent window
        desc_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - desc_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - desc_dialog.winfo_height()) // 2
        desc_dialog.geometry(f"+{x}+{y}")
        
        desc_dialog.wait_window()
    
    def view_history(self):
        """View version history of the current document."""
        if not self.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        try:
            versions = self.doc_manager.get_version_history(self.current_doc_id)
            
            # Create history dialog
            history_dialog = tk.Toplevel(self.root)
            history_dialog.title(f"Version History: {self.current_doc_name}")
            history_dialog.geometry("500x400")
            history_dialog.transient(self.root)
            
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
                
                # Set the diff view to compare these versions
                self.diff_v1_var.set(versions[0])
                self.diff_v2_var.set(versions[1])
                
                # Close the dialog
                history_dialog.destroy()
                
                # Update the diff view and switch to it
                self.update_diff_view()
            
            ttk.Button(button_frame, text="Compare Selected", command=compare_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=history_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Center dialog on parent window
            history_dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - history_dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - history_dialog.winfo_height()) // 2
            history_dialog.geometry(f"+{x}+{y}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load version history: {str(e)}")
    
    def compare_versions(self):
        """Compare two versions of the current document."""
        if not self.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        try:
            # Get available versions
            versions = self.doc_manager.get_version_history(self.current_doc_id)
            if len(versions) < 2:
                messagebox.showinfo("Info", "Need at least 2 versions to compare.")
                return
            
            # Update the diff view combos
            version_numbers = [str(v["version"]) for v in versions]
            
            self.diff_v1_combo["values"] = version_numbers
            self.diff_v2_combo["values"] = version_numbers
            
            # Set default values - typically compare oldest with newest
            if len(version_numbers) >= 2:
                self.diff_v1_var.set(version_numbers[0])
                self.diff_v2_var.set(version_numbers[-1])
            
            # Switch to the diff tab
            self.notebook.select(self.diff_frame)
            
            # Update the diff view
            self.update_diff_view()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compare versions: {str(e)}")
    
    def delete_document(self):
        """Delete the selected document."""
        selection = self.doc_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a document to delete.")
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.documents):
            return
        
        doc_id = list(self.documents.keys())[index]
        doc_name = self.documents[doc_id]["name"]
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{doc_name}'?\nThis cannot be undone."):
            return
        
        try:
            self.doc_manager.delete_document(doc_id)
            messagebox.showinfo("Success", "Document deleted successfully.")
            
            # Clear if current document was deleted
            if self.current_doc_id == doc_id:
                self.clear_document_view()
            
            self.refresh_document_list()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete document: {str(e)}")
    
    def show_about(self):
        """Show about dialog."""
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About Document Version Control")
        about_dialog.geometry("400x300")
        about_dialog.transient(self.root)
        
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
        x = self.root.winfo_x() + (self.root.winfo_width() - about_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - about_dialog.winfo_height()) // 2
        about_dialog.geometry(f"+{x}+{y}")

def main():
    """Main function to start the GUI."""
    root = tk.Tk()
    app = DocumentVersioningGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()