#!/usr/bin/env python3
"""
Test Runner for Document Versioning System

This script runs the tests for the document versioning system
and provides a detailed report of the results.
"""
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
import time


# Import the test class directly
from document_test import TestDocumentVersioningSystem

def run_tests():
    """Run all tests and return the results."""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDocumentVersioningSystem)
    
    # Run the tests
    print("Starting tests for Document Versioning System...")
    print("=" * 70)
    
    # Create a test result object
    result = unittest.TestResult()
    
    # Time the tests
    start_time = time.time()
    suite.run(result)
    end_time = time.time()
    
    # Calculate execution time
    execution_time = end_time - start_time
    
    # Return the result and execution time
    return result, execution_time

def print_test_report(result, execution_time):
    """Print a detailed report of the test results."""
    print("\nTest Results:")
    print("=" * 70)
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passes = total_tests - failures - errors
    
    print(f"Total tests run: {total_tests}")
    print(f"Tests passed:    {passes}")
    print(f"Tests failed:    {failures}")
    print(f"Test errors:     {errors}")
    print(f"Execution time:  {execution_time:.2f} seconds")
    print("-" * 70)
    
    # Print failures
    if failures > 0:
        print("\nTest Failures:")
        print("-" * 70)
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"Failure {i}: {test}")
            print("-" * 50)
            print(traceback)
            print()
    
    # Print errors
    if errors > 0:
        print("\nTest Errors:")
        print("-" * 70)
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"Error {i}: {test}")
            print("-" * 50)
            print(traceback)
            print()
    
    # Print overall result
    print("=" * 70)
    if failures == 0 and errors == 0:
        print("TEST RESULT: SUCCESS - All tests passed!")
    else:
        print("TEST RESULT: FAILURE - Some tests did not pass.")
    print("=" * 70)

def main():
    """Main entry point for the test runner."""
    # Make sure the test directory gets removed after testing
    if os.path.exists("test_docs"):
        import shutil
        shutil.rmtree("test_docs")
    
    try:
        # Run the tests
        result, execution_time = run_tests()
        
        # Print the report
        print_test_report(result, execution_time)
        
        # Return appropriate exit code
        if len(result.failures) > 0 or len(result.errors) > 0:
            return 1
        else:
            return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    finally:
        # Clean up test directory
        if os.path.exists("test_docs"):
            import shutil
            shutil.rmtree("test_docs")

if __name__ == "__main__":
    sys.exit(main())