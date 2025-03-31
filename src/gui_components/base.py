"""
Base component classes for the Document Version Control System.
Includes UIComponent base class and AppState for state management.
"""

import os
import tkinter as tk
from tkinter import messagebox

class UIComponent:
    """Base class for all UI components"""
    
    def __init__(self, parent, app_state):
        """Initialize the component with parent and shared app state"""
        self.parent = parent
        self.app_state = app_state
        self.frame = None
    
    def create_ui(self):
        """Create the UI elements - to be implemented by subclasses"""
        pass
    
    def update(self, **kwargs):
        """Update the component based on changes in app state"""
        pass
    
    def get_frame(self):
        """Return the main frame of this component"""
        return self.frame

class AppState:
    """Shared application state accessible by all components"""
    
    def __init__(self):
        """Initialize application state"""
        # These imports would be from your actual modules
        from document_manager import DocumentManager
        from version_controller import VersionController
        from ai_analyzer import AIDocumentAnalyzer
        
        # Document manager and related services
        self.doc_manager = DocumentManager("my_documents")
        self.version_controller = VersionController(self.doc_manager)
        self.ai_analyzer = AIDocumentAnalyzer()
        
        # Create directory if it doesn't exist
        os.makedirs("my_documents", exist_ok=True)
        
        # Current document state
        self.current_doc_id = None
        self.current_doc_name = None
        self.current_doc_content = None
        self.current_version = None
        
        # Document list state
        self.documents = {}
        
        # Component flags and settings
        self.ai_panel_visible = True
        self.diff_edit_mode = False
        self.auto_refresh = False
        
        # Event callbacks dictionary - components can register for events
        self._callbacks = {}
    
    def register_callback(self, event_name, callback):
        """Register a callback for a specific event"""
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)
    
    def notify(self, event_name, **kwargs):
        """Notify all registered callbacks about an event"""
        if event_name in self._callbacks:
            for callback in self._callbacks[event_name]:
                callback(**kwargs)
    
    def set_current_document(self, doc_id):
        """Set the current document and notify listeners"""
        if not doc_id:
            self.current_doc_id = None
            self.current_doc_name = None
            self.current_doc_content = None
            self.current_version = None
            self.notify("document_cleared")
            return
        
        content, metadata = self.doc_manager.get_document(doc_id)
        
        self.current_doc_id = doc_id
        self.current_doc_name = metadata["name"]
        self.current_doc_content = content
        self.current_version = metadata["current_version"]
        
        # Notify all components that need to update
        self.notify("document_loaded", doc_id=doc_id, metadata=metadata, content=content)
    
    def refresh_document_list(self):
        """Refresh the document list and notify listeners"""
        documents = self.doc_manager.list_documents()
        self.documents = {doc["id"]: doc for doc in documents}
        self.notify("document_list_updated", documents=self.documents)
        
    def update_current_document(self, content, description):
        """Update the current document with new content"""
        if not self.current_doc_id:
            return None
        
        new_version = self.doc_manager.update_document(
            self.current_doc_id, content, description
        )
        
        # Update state and notify
        self.current_version = new_version
        self.current_doc_content = content
        
        self.notify("document_updated", 
                   doc_id=self.current_doc_id, 
                   new_version=new_version,
                   content=content)
        
        return new_version