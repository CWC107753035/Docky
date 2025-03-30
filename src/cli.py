import os
import sys
import argparse
import textwrap
from document_manager import DocumentManager
from version_controller import VersionController
from ai_analyzer import AIDocumentAnalyzer

class DocumentComparisonCLI:
    """Command line interface for document comparison system."""
    
    def __init__(self):
        """Initialize the CLI with document manager, version controller, and AI analyzer."""
        # Initialize components
        self.doc_manager = DocumentManager("documents")
        self.version_controller = VersionController(self.doc_manager)
        
        # Try to get API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        self.ai_analyzer = AIDocumentAnalyzer(api_key=api_key)
        
        # Flag to indicate if AI features are available
        self.ai_available = bool(api_key)
    
    def setup_parser(self):
        """Set up command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Document Comparison System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent("""
            Examples:
              # Create a new document from a file
              python cli.py create -f document.txt -n "My Document"
              
              # List all documents
              python cli.py list
              
              # Show document content
              python cli.py show DOC_ID
              
              # Update document from a file
              python cli.py update DOC_ID -f updated.txt -m "Updated content"
              
              # Compare two versions
              python cli.py compare DOC_ID -v1 1 -v2 2
              
              # Get AI summary
              python cli.py summarize DOC_ID
            """)
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new document")
        create_parser.add_argument("-f", "--file", required=True, help="File to read content from")
        create_parser.add_argument("-n", "--name", required=True, help="Document name")
        create_parser.add_argument("-t", "--type", default="txt", help="Document type/extension")
        
        # List command
        list_parser = subparsers.add_parser("list", help="List all documents")
        
        # Show command
        show_parser = subparsers.add_parser("show", help="Show document content")
        show_parser.add_argument("doc_id", help="Document ID")
        show_parser.add_argument("-v", "--version", type=int, help="Version to show (default: current)")
        
        # Update command
        update_parser = subparsers.add_parser("update", help="Update document")
        update_parser.add_argument("doc_id", help="Document ID")
        update_parser.add_argument("-f", "--file", required=True, help="File to read new content from")
        update_parser.add_argument("-m", "--message", default="", help="Change description")
        
        # History command
        history_parser = subparsers.add_parser("history", help="Show document version history")
        history_parser.add_argument("doc_id", help="Document ID")
        
        # Compare command
        compare_parser = subparsers.add_parser("compare", help="Compare document versions")
        compare_parser.add_argument("doc_id", help="Document ID")
        compare_parser.add_argument("-v1", "--version1", required=True, type=int, help="First version")
        compare_parser.add_argument("-v2", "--version2", required=True, type=int, help="Second version")
        compare_parser.add_argument("--html", action="store_true", help="Generate HTML diff")
        compare_parser.add_argument("--output", help="Output file for HTML diff")
        
        # Branch command
        branch_parser = subparsers.add_parser("branch", help="Create a branch of a document")
        branch_parser.add_argument("doc_id", help="Document ID")
        branch_parser.add_argument("-n", "--name", required=True, help="Branch name")
        branch_parser.add_argument("-v", "--version", type=int, help="Version to branch from (default: current)")
        
        # Merge command
        merge_parser = subparsers.add_parser("merge", help="Merge changes from one document to another")
        merge_parser.add_argument("target_id", help="Target document ID")
        merge_parser.add_argument("source_id", help="Source document ID")
        merge_parser.add_argument("-v", "--version", type=int, help="Source version (default: current)")
        merge_parser.add_argument("-o", "--output", help="Output file for merged content")
        
        # AI Commands (only available if API key is set)
        if self.ai_available:
            # Summarize command
            summarize_parser = subparsers.add_parser("summarize", help="Generate AI summary of document")
            summarize_parser.add_argument("doc_id", help="Document ID")
            summarize_parser.add_argument("-v", "--version", type=int, help="Version to summarize (default: current)")
            
            # Analyze command
            analyze_parser = subparsers.add_parser("analyze", help="Analyze changes between versions")
            analyze_parser.add_argument("doc_id", help="Document ID")
            analyze_parser.add_argument("-v1", "--version1", required=True, type=int, help="First version")
            analyze_parser.add_argument("-v2", "--version2", required=True, type=int, help="Second version")
            
            # Suggest command
            suggest_parser = subparsers.add_parser("suggest", help="Get AI suggestions for document improvements")
            suggest_parser.add_argument("doc_id", help="Document ID")
            suggest_parser.add_argument("-v", "--version", type=int, help="Version to analyze (default: current)")
        
        return parser
    
    def run(self, args=None):
        """Run the CLI with the given arguments."""
        parser = self.setup_parser()
        args = parser.parse_args(args)
        
        if args.command is None:
            parser.print_help()
            return
        
        try:
            # Create document
            if args.command == "create":
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc_id = self.doc_manager.create_document(content, args.name, args.type)
                print(f"Created document with ID: {doc_id}")
            
            # List documents
            elif args.command == "list":
                documents = self.doc_manager.list_documents()
                if documents:
                    print(f"Found {len(documents)} documents:")
                    for doc in documents:
                        print(f"- {doc['name']} (ID: {doc['id']}, Versions: {doc['version_count']})")
                else:
                    print("No documents found.")
            
            # Show document
            elif args.command == "show":
                content, metadata = self.doc_manager.get_document(args.doc_id, args.version)
                version = args.version or metadata["current_version"]
                
                print(f"Document: {metadata['name']} (Version {version})")
                print(f"Type: {metadata['type']}")
                print(f"Updated: {metadata['updated_at']}")
                print("-" * 50)
                print(content)
                print("-" * 50)
            
            # Update document
            elif args.command == "update":
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                version = self.doc_manager.update_document(args.doc_id, content, args.message)
                print(f"Updated document to version {version}")
            
            # History command
            elif args.command == "history":
                versions = self.doc_manager.get_version_history(args.doc_id)
                _, metadata = self.doc_manager.get_document(args.doc_id)
                
                print(f"Version history for document: {metadata['name']} (ID: {args.doc_id})")
                print("-" * 50)
                
                for version in versions:
                    current = " (current)" if version["version"] == metadata["current_version"] else ""
                    print(f"Version {version['version']}{current}:")
                    print(f"  Created: {version['timestamp']}")
                    print(f"  Changes: {version['changes']}")
                    print()
            
            # Compare command
            elif args.command == "compare":
                if args.html:
                    # Generate HTML diff
                    html_diff = self.version_controller.get_diff_html(args.doc_id, args.version1, args.version2)
                    
                    output_file = args.output or f"diff_{args.doc_id}_v{args.version1}_{args.version2}.html"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(html_diff)
                    
                    print(f"HTML diff saved to {output_file}")
                else:
                    # Show text diff
                    changes = self.doc_manager.compare_versions(args.doc_id, args.version1, args.version2)
                    
                    print(f"Changes between versions {args.version1} and {args.version2}:")
                    print("-" * 50)
                    
                    for change in changes:
                        print(f"@@ {change['old_range']} {change['new_range']} @@")
                        for line in change['lines']:
                            prefix = "+" if line['type'] == 'added' else "-" if line['type'] == 'removed' else " "
                            print(f"{prefix} {line['content']}")
                        print()
            
            # Branch command
            elif args.command == "branch":
                branch_id = self.version_controller.create_branch(args.doc_id, args.name, args.version)
                print(f"Created branch with ID: {branch_id}")
            
            # Merge command
            elif args.command == "merge":
                merged_content, conflicts = self.version_controller.merge_changes(
                    args.target_id, args.source_id, args.version)
                
                if conflicts:
                    print(f"Merge has {len(conflicts)} conflicts.")
                    
                    # If AI is available, try to analyze conflicts
                    if self.ai_available and len(conflicts) > 0:
                        print("\nAI conflict analysis:")
                        analysis = self.ai_analyzer.analyze_conflict(conflicts[0])
                        print(analysis)
                
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(merged_content)
                    print(f"Merged content saved to {args.output}")
                    print("Review the merged content and use the 'update' command to save it as a new version.")
                else:
                    print("\nMerged content preview:")
                    print("-" * 50)
                    print(merged_content[:500] + "..." if len(merged_content) > 500 else merged_content)
                    print("-" * 50)
                    print("Use --output option to save the full merged content to a file.")
            
            # AI Commands (only if API key is available)
            elif self.ai_available:
                # Summarize command
                if args.command == "summarize":
                    content, _ = self.doc_manager.get_document(args.doc_id, args.version)
                    summary = self.ai_analyzer.summarize_document(content)
                    
                    print("AI Document Summary:")
                    print("-" * 50)
                    print(summary)
                    print("-" * 50)
                
                # Analyze command
                elif args.command == "analyze":
                    content1, _ = self.doc_manager.get_document(args.doc_id, args.version1)
                    content2, _ = self.doc_manager.get_document(args.doc_id, args.version2)
                    
                    analysis = self.ai_analyzer.compare_versions(content1, content2)
                    
                    print(f"AI Analysis of changes between versions {args.version1} and {args.version2}:")
                    print("-" * 50)
                    print(analysis)
                    print("-" * 50)
                
                # Suggest command
                elif args.command == "suggest":
                    content, _ = self.doc_manager.get_document(args.doc_id, args.version)
                    suggestions = self.ai_analyzer.suggest_improvements(content)
                    
                    print("AI Improvement Suggestions:")
                    print("-" * 50)
                    print(suggestions)
                    print("-" * 50)
            
            else:
                if args.command in ["summarize", "analyze", "suggest"]:
                    print("AI features unavailable: No API key found.")
                    print("To use AI features, set the OPENAI_API_KEY environment variable.")
                else:
                    parser.print_help()
        
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
        
        return 0

def main():
    """Main entry point for the CLI."""
    cli = DocumentComparisonCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())