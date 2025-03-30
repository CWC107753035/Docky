import os
import json
import uuid
import shutil
import datetime
from typing import Dict, List, Optional, Tuple, Any
import difflib

class DocumentManager:
    """Manages document storage, retrieval, and version tracking."""
    
    def __init__(self, base_dir: str = "documents"):
        """
        Initialize the document manager.
        
        Args:
            base_dir: Base directory for storing all documents
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_document(self, content: str, name: str, doc_type: str = "txt") -> str:
        """
        Create a new document with initial content.
        
        Args:
            content: Initial document content
            name: Document name
            doc_type: Document type/extension
            
        Returns:
            Document ID
        """
        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Create document directory
        doc_dir = os.path.join(self.base_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        # Create metadata
        metadata = {
            "name": name,
            "type": doc_type,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "version_count": 1,
            "current_version": 1,
            "versions": [
                {
                    "version": 1,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "changes": "Initial version"
                }
            ]
        }
        
        # Save initial version
        version_path = os.path.join(doc_dir, f"v1.{doc_type}")
        with open(version_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return doc_id
    
    def update_document(self, doc_id: str, content: str, change_description: str = "") -> int:
        """
        Create a new version of an existing document.
        
        Args:
            doc_id: Document ID
            content: New content
            change_description: Description of changes
            
        Returns:
            New version number
        """
        # Check if document exists
        doc_dir = os.path.join(self.base_dir, doc_id)
        if not os.path.exists(doc_dir):
            raise FileNotFoundError(f"Document with ID {doc_id} not found")
        
        # Load metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Increment version
        new_version = metadata["version_count"] + 1
        
        # Save new version
        version_path = os.path.join(doc_dir, f"v{new_version}.{metadata['type']}")
        with open(version_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update metadata
        metadata["version_count"] = new_version
        metadata["current_version"] = new_version
        metadata["updated_at"] = datetime.datetime.now().isoformat()
        metadata["versions"].append({
            "version": new_version,
            "timestamp": datetime.datetime.now().isoformat(),
            "changes": change_description
        })
        
        # Save updated metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return new_version
    
    def get_document(self, doc_id: str, version: Optional[int] = None) -> Tuple[str, Dict]:
        """
        Retrieve a document's content and metadata.
        
        Args:
            doc_id: Document ID
            version: Specific version to retrieve (None for current)
            
        Returns:
            Tuple of (content, metadata)
        """
        # Check if document exists
        doc_dir = os.path.join(self.base_dir, doc_id)
        if not os.path.exists(doc_dir):
            raise FileNotFoundError(f"Document with ID {doc_id} not found")
        
        # Load metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Determine which version to retrieve
        if version is None:
            version = metadata["current_version"]
        elif version < 1 or version > metadata["version_count"]:
            raise ValueError(f"Version {version} does not exist")
        
        # Load content
        version_path = os.path.join(doc_dir, f"v{version}.{metadata['type']}")
        with open(version_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, metadata
    
    def list_documents(self) -> List[Dict]:
        """
        List all documents with their basic metadata.
        
        Returns:
            List of document summaries
        """
        documents = []
        
        # Iterate through document directories
        for doc_id in os.listdir(self.base_dir):
            doc_dir = os.path.join(self.base_dir, doc_id)
            if os.path.isdir(doc_dir):
                metadata_path = os.path.join(doc_dir, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    documents.append({
                        "id": doc_id,
                        "name": metadata["name"],
                        "type": metadata["type"],
                        "updated_at": metadata["updated_at"],
                        "version_count": metadata["version_count"],
                        "current_version": metadata["current_version"]
                    })
        
        return documents
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and all its versions.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        doc_dir = os.path.join(self.base_dir, doc_id)
        if not os.path.exists(doc_dir):
            raise FileNotFoundError(f"Document with ID {doc_id} not found")
        
        # Remove document directory
        shutil.rmtree(doc_dir)
        return True
    
    def get_version_history(self, doc_id: str) -> List[Dict]:
        """
        Get the version history of a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of version entries
        """
        # Check if document exists
        doc_dir = os.path.join(self.base_dir, doc_id)
        if not os.path.exists(doc_dir):
            raise FileNotFoundError(f"Document with ID {doc_id} not found")
        
        # Load metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata["versions"]
    
    def compare_versions(self, doc_id: str, version1: int, version2: int) -> List[Dict]:
        """
        Compare two versions of a document.
        
        Args:
            doc_id: Document ID
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            List of differences
        """
        # Get content of both versions
        content1, _ = self.get_document(doc_id, version1)
        content2, _ = self.get_document(doc_id, version2)
        
        # Split into lines
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Get differences
        diff = list(difflib.unified_diff(
            lines1, 
            lines2, 
            fromfile=f'v{version1}', 
            tofile=f'v{version2}', 
            lineterm='',
            n=3  # Context lines
        ))
        
        # Parse differences
        changes = []
        current_change = None
        
        for line in diff[2:]:  # Skip the header lines
            if line.startswith('@@'):
                # New hunk
                if current_change:
                    changes.append(current_change)
                
                # Extract line numbers
                parts = line.split(' ')
                old_range = parts[1]
                new_range = parts[2]
                
                current_change = {
                    'type': 'hunk',
                    'old_range': old_range,
                    'new_range': new_range,
                    'lines': []
                }
            elif current_change:
                # Content line
                line_type = None
                content = line
                
                if line.startswith('-'):
                    line_type = 'removed'
                    content = line[1:]
                elif line.startswith('+'):
                    line_type = 'added'
                    content = line[1:]
                else:
                    line_type = 'context'
                    content = line[1:] if line.startswith(' ') else line
                
                current_change['lines'].append({
                    'type': line_type,
                    'content': content
                })
        
        # Add the last change
        if current_change:
            changes.append(current_change)
        
        return changes
    
    def set_current_version(self, doc_id: str, version: int) -> bool:
        """
        Set the current version of a document.
        
        Args:
            doc_id: Document ID
            version: Version to set as current
            
        Returns:
            True if successful
        """
        # Check if document exists
        doc_dir = os.path.join(self.base_dir, doc_id)
        if not os.path.exists(doc_dir):
            raise FileNotFoundError(f"Document with ID {doc_id} not found")
        
        # Load metadata
        metadata_path = os.path.join(doc_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Check if version exists
        if version < 1 or version > metadata["version_count"]:
            raise ValueError(f"Version {version} does not exist")
        
        # Update current version
        metadata["current_version"] = version
        metadata["updated_at"] = datetime.datetime.now().isoformat()
        
        # Save updated metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return True