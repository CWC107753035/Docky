#!/usr/bin/env python3
"""
Document Comparison System

This application provides version control and AI-powered analysis for documents.
"""

import os
import sys
from cli import DocumentComparisonCLI

def main():
    """Main entry point for the application."""
    # Check for required directories
    os.makedirs("documents", exist_ok=True)
    
    # Print welcome message
    print("=" * 70)
    print("Document Comparison System")
    print("=" * 70)
    
    # Check if AI features are available
    if not os.environ.get("OPENAI_API_KEY"):
        print("Note: AI features are disabled. To enable them, set the OPENAI_API_KEY")
        print("environment variable with your OpenAI API key.")
        print("-" * 70)
    
    # Run the CLI
    cli = DocumentComparisonCLI()
    return cli.run(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())