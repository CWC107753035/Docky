"""
Diff component for Document Version Control System.
Handles comparing different versions of a document.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import difflib
from datetime import datetime

from .base import UIComponent

class DiffComponent(UIComponent):
    """Document comparison component"""
    
    def __init__(self, parent, app_state):
        super().__init__(parent, app_state)
        
        # Register for events
        self.app_state.register_callback("document_loaded", self.update_version_combos)
        self.app_state.register_callback("document_cleared", self.clear_diff_view)
        self.app_state.register_callback("document_updated", self.update_after_doc_change)
        self.app_state.register_callback("compare_versions", self.set_and_compare_versions)
        self.app_state.register_callback("version_changed", self.auto_refresh_check)
        
        self.create_ui()
    
    def create_ui(self):
        """Create the diff comparison UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Controls frame
        controls_frame = ttk.Frame(self.frame)
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
        
        ttk.Button(controls_frame, text="Compare", 
                 command=self.update_diff_view).pack(side=tk.LEFT, padx=10)
        
        # Add edit mode toggle button
        self.edit_mode_var = tk.StringVar(value="Enable Edit Mode")
        self.edit_mode_btn = ttk.Button(
            controls_frame, 
            textvariable=self.edit_mode_var, 
            command=self.toggle_diff_edit_mode
        )
        self.edit_mode_btn.pack(side=tk.LEFT, padx=10)
        
        # Add save edited version button (initially disabled)
        self.save_edit_btn = ttk.Button(
            controls_frame, 
            text="Save Edited Version", 
            command=self.save_edited_version, 
            state=tk.DISABLED
        )
        self.save_edit_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(controls_frame, text="Auto-Refresh", 
                 command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=10)
        
        # Auto-refresh status
        self.auto_refresh_var = tk.StringVar(value="Auto-Refresh: Off")
        ttk.Label(controls_frame, textvariable=self.auto_refresh_var).pack(side=tk.LEFT, padx=10)
        
        # Create side-by-side frames for comparison
        self.side_by_side_frame = ttk.Frame(self.frame)
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
        def on_left_scroll(*args):
            self.right_text.yview_moveto(self.left_text.yview()[0])
        
        def on_right_scroll(*args):
            self.left_text.yview_moveto(self.right_text.yview()[0])
        
        # Connect for synchronized scrolling
        self.left_text.bind("<MouseWheel>", on_left_scroll)
        self.right_text.bind("<MouseWheel>", on_right_scroll)
        self.left_text.bind("<Key-Up>", on_left_scroll)
        self.left_text.bind("<Key-Down>", on_left_scroll)
        self.right_text.bind("<Key-Up>", on_right_scroll)
        self.right_text.bind("<Key-Down>", on_right_scroll)
        
        # Add an edit status bar
        self.edit_status_var = tk.StringVar(value="")
        self.edit_status_label = ttk.Label(self.frame, textvariable=self.edit_status_var, foreground="blue")
        self.edit_status_label.pack(fill=tk.X, padx=5, pady=(0, 5), anchor=tk.W)
    
    def auto_refresh_check(self, version=None):
        """Check if auto-refresh is on and update the diff view if needed"""
        if self.app_state.auto_refresh:
            self.update_diff_view()
    
    def update_version_combos(self, doc_id, metadata, **kwargs):
        """Update version comboboxes when a document is loaded"""
        # Update version dropdowns
        versions = [str(v["version"]) for v in metadata["versions"]]
        self.diff_v1_combo["values"] = versions
        self.diff_v2_combo["values"] = versions
        
        # Set default values for diff
        if len(versions) >= 2:
            self.diff_v1_var.set(versions[0])
            self.diff_v2_var.set(versions[-1])
        elif len(versions) == 1:
            self.diff_v1_var.set(versions[0])
            self.diff_v2_var.set(versions[0])
    
    def clear_diff_view(self):
        """Clear the diff view"""
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
        if self.app_state.diff_edit_mode:
            self.toggle_diff_edit_mode()
    
    def update_after_doc_change(self, doc_id, new_version, **kwargs):
        """Update diff view after document update if auto-refresh is on"""
        # Add new version to combos if not present
        versions = list(self.diff_v1_combo["values"])
        if str(new_version) not in versions:
            versions.append(str(new_version))
            self.diff_v1_combo["values"] = versions
            self.diff_v2_combo["values"] = versions
        
        # Set right side to new version
        self.diff_v2_var.set(str(new_version))
        
        # Update diff view if auto-refresh is on
        if self.app_state.auto_refresh:
            self.update_diff_view()
    
    def set_and_compare_versions(self, v1, v2):
        """Set the specified versions and compare them"""
        self.diff_v1_var.set(v1)
        self.diff_v2_var.set(v2)
        self.update_diff_view()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh for diff view"""
        self.app_state.auto_refresh = not self.app_state.auto_refresh
        self.auto_refresh_var.set(f"Auto-Refresh: {'On' if self.app_state.auto_refresh else 'Off'}")
        
        # If turning on, update the diff view immediately
        if self.app_state.auto_refresh:
            self.update_diff_view()
    
    def toggle_diff_edit_mode(self):
        """Toggle edit mode in the comparison view"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        self.app_state.diff_edit_mode = not self.app_state.diff_edit_mode
        
        if self.app_state.diff_edit_mode:
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
    
    def update_diff_view(self):
        """
        Update the side-by-side diff view with the selected versions.
        
        Uses the version controller for better diff calculation
        and handles the text widget state properly.
        """
        if not self.app_state.current_doc_id:
            return
        
        try:
            v1 = int(self.diff_v1_var.get())
            v2 = int(self.diff_v2_var.get())
            
            if v1 == v2:
                messagebox.showinfo("Info", "Please select different versions to compare.")
                return
            
            # Get content of both versions
            content1, _ = self.app_state.doc_manager.get_document(self.app_state.current_doc_id, v1)
            content2, _ = self.app_state.doc_manager.get_document(self.app_state.current_doc_id, v2)
            
            # Update headers
            self.left_header_var.set(f"Version: {v1}")
            self.right_header_var.set(f"Version: {v2}")
            
            # Set text widgets to normal for updating
            was_edit_mode = self.app_state.diff_edit_mode
            self.left_text.config(state=tk.NORMAL)
            self.right_text.config(state=tk.NORMAL)
            
            # Clear the text widgets
            self.left_text.delete(1.0, tk.END)
            self.right_text.delete(1.0, tk.END)
            
            # Display the content
            self.left_text.insert(tk.END, content1)
            self.right_text.insert(tk.END, content2)
            
            # Get the changes using version controller for more accurate diff
            changes = self.app_state.version_controller.get_word_diff(
                self.app_state.current_doc_id, v1, v2
            )
            
            # Highlight the differences
            self.highlight_differences(changes, content1, content2)
            
            # Set back to disabled if not in edit mode
            if not was_edit_mode:
                self.left_text.config(state=tk.DISABLED)
                self.right_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate diff: {str(e)}")
            import traceback
            traceback.print_exc()  # This will help with debugging
    
    def highlight_differences(self, changes, content1, content2):
        """Highlight the differences in the side-by-side view"""
        # Split content into lines
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Use difflib for the comparison
        diff = list(difflib.Differ().compare(lines1, lines2))
        
        # Process the diff line by line
        for i, line in enumerate(diff):
            if line.startswith('- '):
                # Line only in left version (removed)
                line_idx = i - sum(1 for l in diff[:i] if l.startswith('+ '))
                if line_idx < len(lines1):
                    start_pos = f"{line_idx + 1}.0"
                    end_pos = f"{line_idx + 1}.end"
                    self.left_text.tag_add("deletion", start_pos, end_pos)
                    
            elif line.startswith('+ '):
                # Line only in right version (added)
                line_idx = i - sum(1 for l in diff[:i] if l.startswith('- '))
                if line_idx < len(lines2):
                    start_pos = f"{line_idx + 1}.0"
                    end_pos = f"{line_idx + 1}.end"
                    self.right_text.tag_add("addition", start_pos, end_pos)
                    
            elif line.startswith('? '):
                # Line with differences (hints from differ)
                pass
            else:
                # Line in both versions (unchanged)
                line_idx_left = i - sum(1 for l in diff[:i] if l.startswith('+ '))
                line_idx_right = i - sum(1 for l in diff[:i] if l.startswith('- '))
                
                # Check if identical lines are in different positions - highlight them
                if line_idx_left < len(lines1) and line_idx_right < len(lines2):
                    # Only highlight if position has changed
                    original_idx = lines1.index(line[2:]) if line[2:] in lines1 else -1
                    new_idx = lines2.index(line[2:]) if line[2:] in lines2 else -1
                    
                    if original_idx != new_idx and original_idx >= 0 and new_idx >= 0:
                        left_start_pos = f"{line_idx_left + 1}.0"
                        left_end_pos = f"{line_idx_left + 1}.end"
                        right_start_pos = f"{line_idx_right + 1}.0"
                        right_end_pos = f"{line_idx_right + 1}.end"
                        
                        self.left_text.tag_add("change", left_start_pos, left_end_pos)
                        self.right_text.tag_add("change", right_start_pos, right_end_pos)
    
    def save_edited_version(self):
        """Save either the left or right version as a new document version"""
        if not self.app_state.current_doc_id or not self.app_state.diff_edit_mode:
            return
        
        # Ask which version to save
        choice_dialog = tk.Toplevel(self.parent)
        choice_dialog.title("Save Edited Version")
        choice_dialog.geometry("400x200")
        choice_dialog.transient(self.parent)
        choice_dialog.grab_set()
        
        ttk.Label(choice_dialog, text="Which version would you like to save?", 
                 font=("Arial", 10, "bold")).pack(pady=(20, 10))
        
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
        x = self.parent.winfo_x() + (self.parent.winfo_width() - choice_dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - choice_dialog.winfo_height()) // 2
        choice_dialog.geometry(f"+{x}+{y}")
        
        choice_dialog.wait_window()
    
    def _open_merge_dialog(self):
        """Open a dialog to create a merged version from both text panes"""
        merge_dialog = tk.Toplevel(self.parent)
        merge_dialog.title("Merge Versions")
        merge_dialog.geometry("700x500")
        merge_dialog.transient(self.parent)
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
        
        ttk.Button(btn_frame, text="Save Merged Version", 
                  command=save_merge).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", 
                  command=merge_dialog.destroy).pack(side=tk.RIGHT)
        
        # Center dialog
        merge_dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - merge_dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - merge_dialog.winfo_height()) // 2
        merge_dialog.geometry(f"+{x}+{y}")
    
    def _save_version_with_description(self, content, default_desc="Edited in compare view"):
        """Save the content as a new version after getting a description"""
        # Ask for change description
        desc_dialog = tk.Toplevel(self.parent)
        desc_dialog.title("Change Description")
        desc_dialog.geometry("400x200")
        desc_dialog.transient(self.parent)
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
                new_version = self.app_state.update_current_document(content, description)
                messagebox.showinfo("Success", f"Document updated to version {new_version}")
                desc_dialog.destroy()
                
                # Turn off edit mode
                if self.app_state.diff_edit_mode:
                    self.toggle_diff_edit_mode()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update document: {str(e)}")
        
        ttk.Button(desc_dialog, text="Save New Version", command=do_update).pack(pady=10)
        
        # Center dialog on parent window
        desc_dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - desc_dialog.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - desc_dialog.winfo_height()) // 2
        desc_dialog.geometry(f"+{x}+{y}")
        
        desc_dialog.wait_window()