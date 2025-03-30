import os
import difflib
from typing import List, Dict, Optional, Tuple
from document_manager import DocumentManager
import json

class VersionController:
    """Handles document version comparison and detailed diff operations."""
    
    def __init__(self, doc_manager: DocumentManager):
        """
        Initialize the version controller.
        
        Args:
            doc_manager: DocumentManager instance
        """
        self.doc_manager = doc_manager
    
    def get_diff_html(self, doc_id: str, version1: int, version2: int) -> str:
        """
        Generate HTML representation of differences between two versions.
        
        Args:
            doc_id: Document ID
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            HTML string with highlighted differences
        """
        # Get content of both versions
        content1, _ = self.doc_manager.get_document(doc_id, version1)
        content2, _ = self.doc_manager.get_document(doc_id, version2)
        
        # Split into lines
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Generate HTML diff
        diff = difflib.HtmlDiff()
        html_diff = diff.make_file(
            lines1, 
            lines2, 
            f"Version {version1}", 
            f"Version {version2}",
            context=True,
            numlines=3
        )
        
        return html_diff
    
    def get_word_diff(self, doc_id: str, version1: int, version2: int) -> List[Dict]:
        """
        Generate word-level diff between two versions.
        
        Args:
            doc_id: Document ID
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            List of word changes
        """
        # Get content of both versions
        content1, _ = self.doc_manager.get_document(doc_id, version1)
        content2, _ = self.doc_manager.get_document(doc_id, version2)
        
        # Tokenize to words
        words1 = content1.split()
        words2 = content2.split()
        
        # Compare with SequenceMatcher
        matcher = difflib.SequenceMatcher(None, words1, words2)
        opcodes = matcher.get_opcodes()
        
        # Build diff result
        result = []
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                result.append({
                    'type': 'equal',
                    'words': words1[i1:i2]
                })
            elif tag == 'replace':
                result.append({
                    'type': 'removed',
                    'words': words1[i1:i2]
                })
                result.append({
                    'type': 'added',
                    'words': words2[j1:j2]
                })
            elif tag == 'delete':
                result.append({
                    'type': 'removed',
                    'words': words1[i1:i2]
                })
            elif tag == 'insert':
                result.append({
                    'type': 'added',
                    'words': words2[j1:j2]
                })
        
        return result
    
    def create_branch(self, doc_id: str, branch_name: str, from_version: Optional[int] = None) -> str:
        """
        Create a new branch (a copy) of the document.
        
        Args:
            doc_id: Document ID
            branch_name: Name for the new branch
            from_version: Version to branch from (None for current)
            
        Returns:
            New document ID (branch)
        """
        # Get document content and metadata
        content, metadata = self.doc_manager.get_document(doc_id, from_version)
        
        # Create new document with the same content
        branch_name_full = f"{metadata['name']} - {branch_name}"
        new_doc_id = self.doc_manager.create_document(
            content, 
            branch_name_full, 
            metadata['type']
        )
        
        # Update metadata to track branch relationship
        doc_dir = os.path.join(self.doc_manager.base_dir, new_doc_id)
        metadata_path = os.path.join(doc_dir, "metadata.json")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            branch_metadata = json.load(f)
        
        # Add branch information
        branch_metadata["branched_from"] = {
            "doc_id": doc_id,
            "version": from_version if from_version else metadata["current_version"],
            "name": metadata["name"]
        }
        
        # Save updated metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(branch_metadata, f, indent=2)
        
        return new_doc_id
    
    def merge_changes(self, doc_id: str, source_doc_id: str, source_version: Optional[int] = None) -> Tuple[str, List[Dict]]:
        """
        Merge changes from one document version to another.
        
        Args:
            doc_id: Target document ID
            source_doc_id: Source document ID
            source_version: Source version (None for current)
            
        Returns:
            Tuple of (merged_content, conflicts)
        """
        # Get source and target content
        source_content, source_meta = self.doc_manager.get_document(source_doc_id, source_version)
        target_content, _ = self.doc_manager.get_document(doc_id)
        
        # Split into lines
        source_lines = source_content.splitlines()
        target_lines = target_content.splitlines()
        
        # Find a common ancestor if available
        common_ancestor_content = None
        if "branched_from" in source_meta and source_meta["branched_from"]["doc_id"] == doc_id:
            # If source was branched from target, use that version as common ancestor
            ancestor_version = source_meta["branched_from"]["version"]
            ancestor_content, _ = self.doc_manager.get_document(doc_id, ancestor_version)
            common_ancestor_content = ancestor_content.splitlines()
        
        # Perform a three-way merge if we have a common ancestor
        conflicts = []
        merged_lines = []
        
        if common_ancestor_content:
            # Use three-way merge
            merger = difflib.Differ()
            # Get differences between ancestor and each version
            diff_ancestor_target = list(merger.compare(common_ancestor_content, target_lines))
            diff_ancestor_source = list(merger.compare(common_ancestor_content, source_lines))
            
            # Process the diffs to create a merged version
            # This is a simplified approach and may need refinement for complex merges
            for i in range(max(len(diff_ancestor_target), len(diff_ancestor_source))):
                if i < len(diff_ancestor_target) and i < len(diff_ancestor_source):
                    target_line = diff_ancestor_target[i]
                    source_line = diff_ancestor_source[i]
                    
                    # Both unchanged or same change
                    if target_line == source_line:
                        if not target_line.startswith('- '):
                            merged_lines.append(target_line[2:] if target_line.startswith('  ') else target_line[2:])
                    # Target changed, source unchanged
                    elif target_line.startswith('+ ') and source_line.startswith('  '):
                        merged_lines.append(target_line[2:])
                    # Source changed, target unchanged
                    elif source_line.startswith('+ ') and target_line.startswith('  '):
                        merged_lines.append(source_line[2:])
                    # Both changed differently
                    elif target_line.startswith('+ ') and source_line.startswith('+ '):
                        conflicts.append({
                            'line': i,
                            'target': target_line[2:],
                            'source': source_line[2:]
                        })
                        # Include both with conflict markers
                        merged_lines.append("<<<<<<< TARGET")
                        merged_lines.append(target_line[2:])
                        merged_lines.append("=======")
                        merged_lines.append(source_line[2:])
                        merged_lines.append(">>>>>>> SOURCE")
                elif i < len(diff_ancestor_target):
                    # Only target has this line
                    target_line = diff_ancestor_target[i]
                    if not target_line.startswith('- '):
                        merged_lines.append(target_line[2:] if target_line.startswith('  ') else target_line[2:])
                else:
                    # Only source has this line
                    source_line = diff_ancestor_source[i]
                    if not source_line.startswith('- '):
                        merged_lines.append(source_line[2:] if source_line.startswith('  ') else source_line[2:])
        else:
            # Simple merge without common ancestor
            # This is more likely to produce conflicts
            matcher = difflib.SequenceMatcher(None, target_lines, source_lines)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # Both versions have these lines
                    merged_lines.extend(target_lines[i1:i2])
                elif tag == 'replace':
                    # Conflict: both versions changed these lines differently
                    conflicts.append({
                        'line_range': (i1, i2),
                        'target': target_lines[i1:i2],
                        'source': source_lines[j1:j2]
                    })
                    # Include both with conflict markers
                    merged_lines.append("<<<<<<< TARGET")
                    merged_lines.extend(target_lines[i1:i2])
                    merged_lines.append("=======")
                    merged_lines.extend(source_lines[j1:j2])
                    merged_lines.append(">>>>>>> SOURCE")
                elif tag == 'delete':
                    # Lines only in target
                    merged_lines.extend(target_lines[i1:i2])
                elif tag == 'insert':
                    # Lines only in source
                    merged_lines.extend(source_lines[j1:j2])
        
        # Join the merged lines
        merged_content = '\n'.join(merged_lines)
        
        return merged_content, conflicts
    
    def resolve_conflict(self, merged_content: str, resolution: Dict) -> str:
        """
        Resolve a merge conflict.
        
        Args:
            merged_content: Content with conflict markers
            resolution: Resolution details
            
        Returns:
            Updated content
        """
        lines = merged_content.splitlines()
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line == "<<<<<<< TARGET":
                # Found a conflict marker
                conflict_start = i
                conflict_middle = None
                conflict_end = None
                
                # Find the end of the conflict
                for j in range(i + 1, len(lines)):
                    if lines[j] == "=======":
                        conflict_middle = j
                    elif lines[j] == ">>>>>>> SOURCE":
                        conflict_end = j
                        break
                
                if conflict_middle and conflict_end:
                    # Process this conflict
                    conflict_id = f"{conflict_start}-{conflict_end}"
                    
                    if conflict_id in resolution:
                        choice = resolution[conflict_id]
                        if choice == "target":
                            # Use target content
                            result.extend(lines[conflict_start + 1:conflict_middle])
                        elif choice == "source":
                            # Use source content
                            result.extend(lines[conflict_middle + 1:conflict_end])
                        elif choice == "both":
                            # Use both
                            result.extend(lines[conflict_start + 1:conflict_middle])
                            result.extend(lines[conflict_middle + 1:conflict_end])
                        elif choice == "custom":
                            # Use custom content
                            result.append(resolution[f"{conflict_id}_custom"])
                    else:
                        # No resolution provided, keep conflict markers
                        result.extend(lines[conflict_start:conflict_end + 1])
                    
                    i = conflict_end + 1
                    continue
            
            result.append(line)
            i += 1
        
        return '\n'.join(result)