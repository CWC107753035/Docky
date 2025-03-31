"""
AI Analysis component for Document Version Control System.
Handles AI-powered analysis and suggestions for documents.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

from .base import UIComponent

class AIAnalysisComponent(UIComponent):
    """AI document analysis component"""
    
    def __init__(self, parent, app_state):
        super().__init__(parent, app_state)
        
        # Register for events
        self.app_state.register_callback("document_loaded", self.clear_analysis)
        self.app_state.register_callback("document_cleared", self.clear_analysis)
        
        # AI panel visibility state
        self.summary_panel_visible = True
        
        self.create_ui()
    
    def create_ui(self):
        """Create the AI analysis UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Main container
        self.ai_container = ttk.Frame(self.frame)
        self.ai_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top section - Controls
        controls_frame = ttk.Frame(self.ai_container)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(controls_frame, text="AI Analysis Options:").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Summarize Document", 
                 command=self.summarize_document).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Suggest Improvements", 
                 command=self.suggest_improvements).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Analyze Changes", 
                 command=self.analyze_changes).pack(side=tk.LEFT, padx=5)
        
        # Progress indicator
        self.ai_progress_var = tk.StringVar(value="")
        self.ai_progress_label = ttk.Label(controls_frame, textvariable=self.ai_progress_var, foreground="blue")
        self.ai_progress_label.pack(side=tk.RIGHT, padx=10)
        
        # Split the rest of the container into top and bottom sections
        self.ai_paned = ttk.PanedWindow(self.ai_container, orient=tk.VERTICAL)
        self.ai_paned.pack(fill=tk.BOTH, expand=True)
        
        # Summary section (collapsible)
        self.summary_frame = ttk.Frame(self.ai_paned)
        self.ai_paned.add(self.summary_frame, weight=1)
        
        # Summary header with toggle button
        summary_header = ttk.Frame(self.summary_frame)
        summary_header.pack(fill=tk.X)
        
        self.summary_toggle_var = tk.StringVar(value="▼ AI Summary")
        ttk.Button(summary_header, textvariable=self.summary_toggle_var, 
                 command=self.toggle_summary).pack(side=tk.LEFT)
        
        # Summary content
        self.summary_content = ttk.Frame(self.summary_frame)
        self.summary_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_content, height=8, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.insert(tk.END, "AI summary will appear here.")
        self.summary_text.config(state=tk.DISABLED)
        
        # Document with AI comments section
        self.ai_document_frame = ttk.Frame(self.ai_paned)
        self.ai_paned.add(self.ai_document_frame, weight=3)
        
        # Create a horizontal paned window for document and comments
        self.doc_comment_paned = ttk.PanedWindow(self.ai_document_frame, orient=tk.HORIZONTAL)
        self.doc_comment_paned.pack(fill=tk.BOTH, expand=True)
        
        # Document content
        doc_frame = ttk.Frame(self.doc_comment_paned)
        self.doc_comment_paned.add(doc_frame, weight=3)
        
        ttk.Label(doc_frame, text="Document Content:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.ai_doc_text = scrolledtext.ScrolledText(doc_frame, wrap=tk.WORD)
        self.ai_doc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Comments panel
        comments_frame = ttk.Frame(self.doc_comment_paned)
        self.doc_comment_paned.add(comments_frame, weight=1)
        
        ttk.Label(comments_frame, text="AI Suggestions:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.comments_text = scrolledtext.ScrolledText(comments_frame, wrap=tk.WORD, bg="#f5f5f5")
        self.comments_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.comments_text.insert(tk.END, "AI suggestions will appear here.")
        self.comments_text.config(state=tk.DISABLED)
    
    def toggle_summary(self):
        """Toggle the visibility of the summary section"""
        if self.summary_panel_visible:
            self.summary_content.pack_forget()
            self.summary_toggle_var.set("► AI Summary")
            self.summary_panel_visible = False
        else:
            self.summary_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.summary_toggle_var.set("▼ AI Summary")
            self.summary_panel_visible = True
    
    def clear_analysis(self, **kwargs):
        """Clear all AI analysis panels"""
        # Clear the summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, "AI summary will appear here.")
        self.summary_text.config(state=tk.DISABLED)
        
        # Clear suggestions
        self.comments_text.config(state=tk.NORMAL)
        self.comments_text.delete(1.0, tk.END)
        self.comments_text.insert(tk.END, "AI suggestions will appear here.")
        self.comments_text.config(state=tk.DISABLED)
        
        # Clear document display
        self.ai_doc_text.delete(1.0, tk.END)
    
    def summarize_document(self):
        """Generate an AI summary of the current document"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        try:
            # Get the current content
            content = self.app_state.current_doc_content
            if not content or not content.strip():
                messagebox.showinfo("Info", "Document is empty.")
                return
            
            # Show progress
            self.ai_progress_var.set("Generating summary...")
            
            # Run in a separate thread to keep UI responsive
            def run_analysis():
                try:
                    summary = self.app_state.ai_analyzer.summarize_document(content)
                    
                    # Update UI in main thread
                    self.parent.after(0, lambda: self.update_summary(summary))
                except Exception as e:
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"AI analysis failed: {str(e)}"))
                finally:
                    self.parent.after(0, lambda: self.ai_progress_var.set(""))
            
            threading.Thread(target=run_analysis, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start AI analysis: {str(e)}")
    
    def update_summary(self, summary):
        """Update the summary text with AI-generated content"""
        # Make sure the summary section is visible
        if not self.summary_panel_visible:
            self.toggle_summary()
        
        # Update the summary text
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
        
        # Also update the document display in the AI tab
        self.ai_doc_text.delete(1.0, tk.END)
        self.ai_doc_text.insert(tk.END, self.app_state.current_doc_content)
    
    def suggest_improvements(self):
        """Generate AI suggestions for improving the document"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        try:
            # Get the current content
            content = self.app_state.current_doc_content
            if not content or not content.strip():
                messagebox.showinfo("Info", "Document is empty.")
                return
            
            # Show progress
            self.ai_progress_var.set("Generating suggestions...")
            
            # Run in a separate thread
            def run_analysis():
                try:
                    suggestions = self.app_state.ai_analyzer.suggest_improvements(content)
                    
                    # Update UI in main thread
                    self.parent.after(0, lambda: self.update_suggestions(suggestions))
                except Exception as e:
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"AI analysis failed: {str(e)}"))
                finally:
                    self.parent.after(0, lambda: self.ai_progress_var.set(""))
            
            threading.Thread(target=run_analysis, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start AI analysis: {str(e)}")
    
    def update_suggestions(self, suggestions):
        """Update the comments panel with AI-generated suggestions"""
        # Update the comments text
        self.comments_text.config(state=tk.NORMAL)
        self.comments_text.delete(1.0, tk.END)
        self.comments_text.insert(tk.END, suggestions)
        self.comments_text.config(state=tk.DISABLED)
        
        # Also update the document display in the AI tab
        self.ai_doc_text.delete(1.0, tk.END)
        self.ai_doc_text.insert(tk.END, self.app_state.current_doc_content)
    
    def analyze_changes(self):
        """Analyze changes between versions"""
        if not self.app_state.current_doc_id:
            messagebox.showinfo("Info", "No document is currently open.")
            return
        
        # Open dialog to select versions for comparison
        versions_dialog = tk.Toplevel(self.parent)
        versions_dialog.title("Select Versions to Compare")
        versions_dialog.geometry("300x150")
        versions_dialog.transient(self.parent)
        versions_dialog.grab_set()
        
        ttk.Label(versions_dialog, text="Select versions to compare:").pack(pady=(10, 5))
        
        # Get available versions
        try:
            versions = self.app_state.doc_manager.get_version_history(self.app_state.current_doc_id)
            version_numbers = [str(v["version"]) for v in versions]
            
            frame = ttk.Frame(versions_dialog)
            frame.pack(pady=5)
            
            ttk.Label(frame, text="From version:").grid(row=0, column=0, padx=5, pady=5)
            ttk.Label(frame, text="To version:").grid(row=1, column=0, padx=5, pady=5)
            
            v1_var = tk.StringVar(value=version_numbers[0] if version_numbers else "")
            v2_var = tk.StringVar(value=version_numbers[-1] if len(version_numbers) > 1 else v1_var.get())
            
            v1_combo = ttk.Combobox(frame, textvariable=v1_var, values=version_numbers, width=10)
            v2_combo = ttk.Combobox(frame, textvariable=v2_var, values=version_numbers, width=10)
            
            v1_combo.grid(row=0, column=1, padx=5, pady=5)
            v2_combo.grid(row=1, column=1, padx=5, pady=5)
            
            def do_compare():
                try:
                    v1 = int(v1_var.get())
                    v2 = int(v2_var.get())
                    
                    if v1 == v2:
                        messagebox.showinfo("Info", "Please select different versions.")
                        return
                    
                    versions_dialog.destroy()
                    self._perform_change_analysis(v1, v2)
                except ValueError:
                    messagebox.showerror("Error", "Invalid version numbers.")
            
            ttk.Button(versions_dialog, text="Compare", command=do_compare).pack(pady=10)
            
            # Center dialog
            versions_dialog.update_idletasks()
            x = self.parent.winfo_x() + (self.parent.winfo_width() - versions_dialog.winfo_width()) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - versions_dialog.winfo_height()) // 2
            versions_dialog.geometry(f"+{x}+{y}")
            
        except Exception as e:
            versions_dialog.destroy()
            messagebox.showerror("Error", f"Failed to get version history: {str(e)}")
    
    def _perform_change_analysis(self, v1, v2):
        """Perform analysis on the changes between two versions"""
        try:
            # Get content of both versions
            content1, _ = self.app_state.doc_manager.get_document(self.app_state.current_doc_id, v1)
            content2, _ = self.app_state.doc_manager.get_document(self.app_state.current_doc_id, v2)
            
            # Show progress
            self.ai_progress_var.set("Analyzing changes...")
            
            # Run in a separate thread
            def run_analysis():
                try:
                    analysis = self.app_state.ai_analyzer.compare_versions(content1, content2)
                    
                    # Update UI in main thread
                    self.parent.after(0, lambda: self.update_change_analysis(analysis, content2))
                except Exception as e:
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"AI analysis failed: {str(e)}"))
                finally:
                    self.parent.after(0, lambda: self.ai_progress_var.set(""))
            
            threading.Thread(target=run_analysis, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load versions for analysis: {str(e)}")
    
    def update_change_analysis(self, analysis, content):
        """Update the UI with change analysis results"""
        # Update the summary with the analysis
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, analysis)
        self.summary_text.config(state=tk.DISABLED)
        
        # Make sure the summary section is visible
        if not self.summary_panel_visible:
            self.toggle_summary()
        
        # Update the document display with the newer version
        self.ai_doc_text.delete(1.0, tk.END)
        self.ai_doc_text.insert(tk.END, content)
        
        # Clear any previous suggestions
        self.comments_text.config(state=tk.NORMAL)
        self.comments_text.delete(1.0, tk.END)
        self.comments_text.insert(tk.END, "Select 'Suggest Improvements' for AI recommendations.")
        self.comments_text.config(state=tk.DISABLED)