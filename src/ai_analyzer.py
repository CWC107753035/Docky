import os
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
import difflib
import re
import time

class AIDocumentAnalyzer:
    """Provides AI-powered analysis of documents and document versions."""
    
    def __init__(self, api_key: Optional[str] = None, api_type: str = "ollama"):
        """
        Initialize the AI document analyzer.
        
        Args:
            api_key: API key for the AI service (only needed for OpenAI/HuggingFace)
            api_type: Type of AI API to use ("ollama", "openai", "huggingface")
        """
        self.api_key = api_key
        self.api_type = api_type
        self.ollama_host = "http://localhost:11434"
        self.ollama_model = "llama3"  # Default model - can be changed
        
        if self.api_type == "openai" and not self.api_key:
            print("Warning: No API key provided for OpenAI. Please set an API key.")
        elif self.api_type == "huggingface" and not self.api_key:
            print("Warning: No API key provided for Hugging Face. Please set an API key.")
    
    def set_ollama_model(self, model_name: str):
        """
        Set the Ollama model to use.
        
        Args:
            model_name: Name of the model (e.g., "llama3", "mistral", etc.)
        """
        self.ollama_model = model_name
    
    def set_ollama_host(self, host: str):
        """
        Set the Ollama host address.
        
        Args:
            host: Host address (e.g., "http://localhost:11434")
        """
        self.ollama_host = host
    
    def _call_openai_api(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Call the OpenAI API.
        
        Args:
            prompt: The prompt to send to the API
            model: The model to use
            
        Returns:
            The response text
        """
        if not self.api_key:
            return "Error: No OpenAI API key provided."
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # Lower temperature for more deterministic responses
                "max_tokens": 800
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"Error {response.status_code}: {response.text}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_huggingface_api(self, prompt: str, model: str = "google/flan-t5-xl") -> str:
        """
        Call the Hugging Face Inference API.
        
        Args:
            prompt: The prompt to send to the API
            model: The model to use
            
        Returns:
            The response text
        """
        if not self.api_key:
            return "Error: No Hugging Face API key provided."
        
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            payload = {"inputs": prompt}
            
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()[0]["generated_text"]
            else:
                return f"Error {response.status_code}: {response.text}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_ollama_api(self, prompt: str) -> str:
        """
        Call the Ollama API.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response text
        """
        try:
            data = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,  # Lower temperature for more deterministic responses
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                return f"Error {response.status_code}: {response.text}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_ai_api(self, prompt: str) -> str:
        """
        Call the appropriate AI API based on the configured type.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response text
        """
        if self.api_type == "openai":
            return self._call_openai_api(prompt)
        elif self.api_type == "huggingface":
            return self._call_huggingface_api(prompt)
        elif self.api_type == "ollama":
            return self._call_ollama_api(prompt)
        else:
            return f"Error: Unsupported API type '{self.api_type}'"
    
    def _fallback_analysis(self, content: str) -> str:
        """
        Provide a basic analysis without using an external API.
        This is used when no API key is available or API calls fail.
        
        Args:
            content: Document content to analyze
            
        Returns:
            Analysis text
        """
        # Split into paragraphs
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        # Count words
        words = re.findall(r'\b\w+\b', content)
        word_count = len(words)
        
        # Identify headings (assuming markdown-style headings)
        headings = []
        for line in content.splitlines():
            if line.strip().startswith('#'):
                headings.append(line.strip())
        
        # Generate a simple summary
        summary = []
        summary.append(f"Document contains {len(paragraphs)} paragraphs and {word_count} words.")
        
        if headings:
            summary.append(f"Document has {len(headings)} headings:")
            for h in headings[:5]:  # Limit to first 5 headings
                summary.append(f"- {h}")
            if len(headings) > 5:
                summary.append(f"... and {len(headings) - 5} more.")
        
        # Check for code blocks
        code_blocks = re.findall(r'```[^`]*```', content, re.DOTALL)
        if code_blocks:
            summary.append(f"Document contains {len(code_blocks)} code blocks.")
        
        # Get first paragraph as excerpt (if available)
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 200:
                first_para = first_para[:197] + "..."
            summary.append(f"\nExcerpt: {first_para}")
        
        return "\n".join(summary)
    
    def is_ollama_available(self) -> bool:
        """
        Check if Ollama is available.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def list_available_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []
    
    def summarize_document(self, content: str) -> str:
        """
        Generate a summary of a document.
        
        Args:
            content: Document content to summarize
            
        Returns:
            Document summary
        """
        if self.api_type == "ollama" and not self.is_ollama_available():
            return "Error: Ollama service is not available. Please ensure Ollama is running."
        
        prompt = f"""
        Please provide a concise summary of the following document. Focus on:
        1. The main topic and purpose
        2. Key points or arguments
        3. Important sections or structural elements
        4. Any conclusions or recommendations

        Document:
        ```
        {content[:4000]}  # Truncate to avoid exceeding token limits
        ```

        If the document appears to be truncated, please note that in your summary.
        """
        
        try:
            response = self._call_ai_api(prompt)
            return response
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return self._fallback_analysis(content)
    
    def compare_versions(self, old_content: str, new_content: str) -> str:
        """
        Generate an analysis of changes between document versions.
        
        Args:
            old_content: Previous version content
            new_content: New version content
            
        Returns:
            Analysis of changes
        """
        if self.api_type == "ollama" and not self.is_ollama_available():
            return "Error: Ollama service is not available. Please ensure Ollama is running."
            
        # Create a diff for context
        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            lineterm='',
            n=3
        ))
        
        diff_text = "\n".join(diff_lines[:100])  # Limit diff context to avoid token limits
        
        prompt = f"""
        I'm going to provide two versions of a document and their diff. Please analyze the changes between them and provide:
        
        1. A high-level summary of what changed
        2. The significance of these changes
        3. Any suggestions for improving clarity or addressing issues in the revisions
        
        Old version excerpt:
        ```
        {old_content[:2000]}  # Truncated for token limits
        ```
        
        New version excerpt:
        ```
        {new_content[:2000]}  # Truncated for token limits
        ```
        
        Diff (unified format):
        ```
        {diff_text}
        ```
        
        If the document appears to be truncated, please note that in your analysis.
        """
        
        try:
            response = self._call_ai_api(prompt)
            return response
        except Exception as e:
            print(f"Error calling AI API: {e}")
            # Fall back to basic diff analysis
            return self._fallback_analysis_diff(old_content, new_content)
    
    def _fallback_analysis_diff(self, old_content: str, new_content: str) -> str:
        """
        Provide a basic diff analysis without using an external API.
        
        Args:
            old_content: Previous version content
            new_content: New version content
            
        Returns:
            Basic diff analysis
        """
        # Calculate simple metrics
        old_words = len(re.findall(r'\b\w+\b', old_content))
        new_words = len(re.findall(r'\b\w+\b', new_content))
        
        diff = list(difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            lineterm='',
            n=3
        ))
        
        summary = ["Basic Change Analysis:"]
        
        additions = 0
        deletions = 0
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        word_diff = new_words - old_words
        
        summary.append(f"- {additions} lines added")
        summary.append(f"- {deletions} lines removed")
        summary.append(f"- Word count changed from {old_words} to {new_words} ({word_diff:+d} words)")
        
        return "\n".join(summary)
    
    def suggest_improvements(self, content: str) -> str:
        """
        Generate suggestions for improving a document.
        
        Args:
            content: Document content to analyze
            
        Returns:
            Improvement suggestions
        """
        if self.api_type == "ollama" and not self.is_ollama_available():
            return "Error: Ollama service is not available. Please ensure Ollama is running."
        
        prompt = f"""
        Please review the following document and provide specific suggestions for improvement. Focus on:
        
        1. Clarity and organization
        2. Grammar and style
        3. Strengthening arguments or explanations
        4. Adding missing information or context
        5. Overall structure and flow
        
        Document:
        ```
        {content[:4000]}  # Truncated for token limits
        ```
        
        If the document appears to be truncated, please note that in your suggestions.
        """
        
        try:
            response = self._call_ai_api(prompt)
            return response
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return "Sorry, I couldn't generate improvement suggestions at this time."
    
    def analyze_conflict(self, conflict_content: Dict) -> str:
        """
        Analyze a merge conflict and recommend a resolution.
        
        Args:
            conflict_content: Dictionary with conflict information
            
        Returns:
            Conflict analysis and recommendation
        """
        if self.api_type == "ollama" and not self.is_ollama_available():
            return "Error: Ollama service is not available. Please ensure Ollama is running."
        
        # Format the conflict information for the prompt
        target_content = "\n".join(conflict_content.get('target', []))
        source_content = "\n".join(conflict_content.get('source', []))
        
        prompt = f"""
        I'm resolving a merge conflict between two versions of a document. Please analyze the conflict and recommend the best resolution:
        
        Version A (Target):
        ```
        {target_content}
        ```
        
        Version B (Source):
        ```
        {source_content}
        ```
        
        Analyze:
        1. The key differences between these versions
        2. Which version better maintains the document's coherence and purpose
        3. Whether it's better to choose one version entirely or create a hybrid
        
        If you recommend a hybrid approach, please provide the exact text that should be used.
        """
        
        try:
            response = self._call_ai_api(prompt)
            return response
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return "Sorry, I couldn't analyze the conflict at this time."
    
    def batch_analyze(self, doc_id: str, versions: List[int], doc_manager) -> Dict:
        """
        Perform batch analysis on multiple versions of a document.
        
        Args:
            doc_id: Document ID
            versions: List of version numbers to analyze
            doc_manager: Document manager instance
            
        Returns:
            Dictionary of analysis results
        """
        if self.api_type == "ollama" and not self.is_ollama_available():
            return {"error": "Ollama service is not available. Please ensure Ollama is running."}
        
        results = {}
        
        for i, version in enumerate(versions):
            print(f"Analyzing version {version}...")
            
            # Get document content
            content, metadata = doc_manager.get_document(doc_id, version)
            
            # Generate summary
            summary = self.summarize_document(content)
            
            # If not the first version, compare with previous
            comparison = None
            if i > 0:
                prev_version = versions[i-1]
                prev_content, _ = doc_manager.get_document(doc_id, prev_version)
                comparison = self.compare_versions(prev_content, content)
                
                # Small delay to prevent overloading local Ollama
                time.sleep(0.5)
            
            # Store results
            results[version] = {
                "summary": summary,
                "comparison_with_previous": comparison,
                "timestamp": metadata.get("versions", [])[version-1].get("timestamp")
            }
            
            # Small delay to prevent overloading local Ollama
            time.sleep(0.5)
        
        return results