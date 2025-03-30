import os
import shutil
import unittest
from document_manager import DocumentManager
from version_controller import VersionController

class TestDocumentVersioningSystem(unittest.TestCase):
    """Test cases for the document versioning system."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Use a test directory
        self.test_dir = "test_docs"
        
        # Clean up any existing test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Initialize components
        self.doc_manager = DocumentManager(self.test_dir)
        self.version_controller = VersionController(self.doc_manager)
        
        # Sample document content
        self.initial_content = """# Test Document
This is a sample document for testing.

## Section 1
This is the first section of the document.
It contains multiple lines and paragraphs.

## Section 2
This is the second section.
"""

        self.updated_content = """# Test Document (Updated)
This is a sample document for testing.

## Section 1
This is the first section of the document.
It contains multiple lines and paragraphs.
I've added this line to test changes.

## Section 2
This is the second section with some changes.

## Section 3
This is a new section added in version 2.
"""

        self.branch_content = """# Test Document (Branch)
This is a sample document for testing in a branch.

## Section 1
This section has been modified in the branch.
It contains different content than the main document.

## Section 2
This is the second section.

## Branch Section
This section only exists in the branch.
"""
    
    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_document_creation(self):
        """Test document creation and retrieval."""
        # Create document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        
        # Verify document exists
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, doc_id)))
        
        # Retrieve document
        content, metadata = self.doc_manager.get_document(doc_id)
        
        # Verify content and metadata
        self.assertEqual(content, self.initial_content)
        self.assertEqual(metadata["name"], "Test Doc")
        self.assertEqual(metadata["type"], "md")
        self.assertEqual(metadata["version_count"], 1)
        self.assertEqual(metadata["current_version"], 1)
    
    def test_document_update(self):
        """Test document updating."""
        # Create document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        
        # Update document
        new_version = self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Verify version number
        self.assertEqual(new_version, 2)
        
        # Retrieve updated document
        content, metadata = self.doc_manager.get_document(doc_id)
        
        # Verify content and metadata
        self.assertEqual(content, self.updated_content)
        self.assertEqual(metadata["version_count"], 2)
        self.assertEqual(metadata["current_version"], 2)
        self.assertEqual(len(metadata["versions"]), 2)
        self.assertEqual(metadata["versions"][1]["version"], 2)
        self.assertEqual(metadata["versions"][1]["changes"], "Added new section")
    
    def test_version_retrieval(self):
        """Test retrieving specific versions."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Retrieve version 1
        content_v1, _ = self.doc_manager.get_document(doc_id, 1)
        self.assertEqual(content_v1, self.initial_content)
        
        # Retrieve version 2
        content_v2, _ = self.doc_manager.get_document(doc_id, 2)
        self.assertEqual(content_v2, self.updated_content)
    
    def test_version_comparison(self):
        """Test comparing document versions."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Compare versions
        changes = self.doc_manager.compare_versions(doc_id, 1, 2)
        
        # Verify changes were detected
        self.assertTrue(len(changes) > 0)
        
        # Check if changes are in the expected format
        for change in changes:
            self.assertIn('type', change)
            self.assertIn('old_range', change)
            self.assertIn('new_range', change)
            self.assertIn('lines', change)
            
            # Check if line changes are detected correctly
            has_changes = False
            for line in change['lines']:
                if line['type'] in ['added', 'removed']:
                    has_changes = True
                    break
            
            self.assertTrue(has_changes)
    
    def test_html_diff(self):
        """Test HTML diff generation."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Generate HTML diff
        html_diff = self.version_controller.get_diff_html(doc_id, 1, 2)
        
        # Verify HTML was generated
        self.assertTrue(len(html_diff) > 0)
        
        # Python's difflib.HtmlDiff().make_file() actually starts with <html>
        # rather than <!DOCTYPE html>, so check for that instead
        self.assertTrue('<html>' in html_diff.lower())
        
        # Check for key HTML elements
        self.assertIn('<table', html_diff)
        self.assertIn('Version 1', html_diff)
        self.assertIn('Version 2', html_diff)
    
    def test_word_diff(self):
        """Test word-level diff generation."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Generate word diff
        word_diff = self.version_controller.get_word_diff(doc_id, 1, 2)
        
        # Verify word diff was generated
        self.assertTrue(len(word_diff) > 0)
        
        # Check if diff captures additions and removals
        found_added = False
        found_removed = False
        
        for diff in word_diff:
            if diff['type'] == 'added' and len(diff['words']) > 0:
                found_added = True
            elif diff['type'] == 'removed' and len(diff['words']) > 0:
                found_removed = True
        
        # Since we added text in the updated version, we should have additions
        self.assertTrue(found_added)
    
    def test_document_branching(self):
        """Test document branching."""
        # Create document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        
        # Create branch
        branch_id = self.version_controller.create_branch(doc_id, "Test Branch")
        
        # Verify branch exists
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, branch_id)))
        
        # Retrieve branch document
        content, metadata = self.doc_manager.get_document(branch_id)
        
        # Verify content and metadata
        self.assertEqual(content, self.initial_content)
        self.assertIn("Test Branch", metadata["name"])
        
        # Update branch
        self.doc_manager.update_document(branch_id, self.branch_content, "Updated branch")
        
        # Verify branch and original are different
        branch_content, _ = self.doc_manager.get_document(branch_id)
        original_content, _ = self.doc_manager.get_document(doc_id)
        
        self.assertNotEqual(branch_content, original_content)
        self.assertEqual(branch_content, self.branch_content)
    
    def test_version_setting(self):
        """Test setting the current version."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Get current version (should be 2)
        _, metadata = self.doc_manager.get_document(doc_id)
        self.assertEqual(metadata["current_version"], 2)
        
        # Set current version to 1
        self.doc_manager.set_current_version(doc_id, 1)
        
        # Verify current version changed
        _, metadata = self.doc_manager.get_document(doc_id)
        self.assertEqual(metadata["current_version"], 1)
        
        # Get content (should be version 1)
        content, _ = self.doc_manager.get_document(doc_id)
        self.assertEqual(content, self.initial_content)
    
    def test_document_listing(self):
        """Test listing all documents."""
        # Create two documents
        doc_id1 = self.doc_manager.create_document(self.initial_content, "Test Doc 1", "md")
        doc_id2 = self.doc_manager.create_document(self.initial_content, "Test Doc 2", "md")
        
        # List documents
        documents = self.doc_manager.list_documents()
        
        # Verify both documents are listed
        self.assertEqual(len(documents), 2)
        
        # Verify document IDs
        doc_ids = [doc["id"] for doc in documents]
        self.assertIn(doc_id1, doc_ids)
        self.assertIn(doc_id2, doc_ids)
    
    def test_version_history(self):
        """Test retrieving version history."""
        # Create and update document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        self.doc_manager.update_document(doc_id, self.updated_content, "Added new section")
        
        # Get version history
        versions = self.doc_manager.get_version_history(doc_id)
        
        # Verify version count
        self.assertEqual(len(versions), 2)
        
        # Verify version details
        self.assertEqual(versions[0]["version"], 1)
        self.assertEqual(versions[1]["version"], 2)
        self.assertEqual(versions[1]["changes"], "Added new section")
    
    def test_document_deletion(self):
        """Test document deletion."""
        # Create document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        
        # Verify document exists
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, doc_id)))
        
        # Delete document
        self.doc_manager.delete_document(doc_id)
        
        # Verify document was deleted
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, doc_id)))
        
        # Verify listing doesn't include deleted document
        documents = self.doc_manager.list_documents()
        doc_ids = [doc["id"] for doc in documents]
        self.assertNotIn(doc_id, doc_ids)
    
    def test_merge_changes(self):
        """Test merging changes between documents."""
        # Create original document
        doc_id = self.doc_manager.create_document(self.initial_content, "Test Doc", "md")
        
        # Create branch
        branch_id = self.version_controller.create_branch(doc_id, "Test Branch")
        
        # Update both original and branch differently
        self.doc_manager.update_document(doc_id, self.updated_content, "Updated original")
        self.doc_manager.update_document(branch_id, self.branch_content, "Updated branch")
        
        # Merge changes
        merged_content, conflicts = self.version_controller.merge_changes(doc_id, branch_id)
        
        # Verify merged content exists
        self.assertTrue(len(merged_content) > 0)
        
        # Check if both documents contributed to the merge
        # Check for text unique to the updated content
        self.assertIn("Section 3", merged_content)
        
        # Check for text unique to the branch content
        self.assertIn("Branch Section", merged_content)
        
        # There should be conflicts due to the different changes
        # Check if conflicts were detected
        self.assertTrue(len(conflicts) > 0)

# This allows the file to be run directly
if __name__ == "__main__":
    unittest.main()