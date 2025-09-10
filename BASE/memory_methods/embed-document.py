#!/usr/bin/env python3
"""
Batch Document Embedding Script for RAG System
Processes all files in a directory and saves embeddings to another directory
Usage: python embed_document.py
"""

import sys
import json
import os
import requests
from typing import List, Dict, Any
import hashlib
import re
from pathlib import Path

class DocumentEmbedder:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.embed_model = "nomic-embed-text"
        
        # Get the script's directory and build paths relative to it
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent.parent  # Go up two levels from BASE/memory_methods to Esther_AI
        
        # Define the directory paths
        self.input_dir = base_dir / "personality" / "memory_base" / "base_files"
        self.output_dir = base_dir / "personality" / "memory_base" / "base_memory"
        
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If we're not at the end, try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
                
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def load_document(self, filepath: Path) -> str:
        """Load document content from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'utf-16']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise Exception(f"Unable to decode file {filepath}")
    
    def embed_document(self, filepath: Path) -> Dict[str, Any]:
        """Process document and create embeddings."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found")
        
        print(f"Loading document: {filepath}")
        text = self.load_document(filepath)
        
        print(f"Document loaded. Length: {len(text)} characters")
        
        # Create chunks
        print("Chunking document...")
        chunks = self.chunk_text(text)
        print(f"Created {len(chunks)} chunks")
        
        # Create embeddings
        print("Creating embeddings...")
        embeddings_data = {
            "source_file": str(filepath),
            "total_chunks": len(chunks),
            "embed_model": self.embed_model,
            "chunks": []
        }
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            embedding = self.get_embedding(chunk)
            
            if embedding:
                chunk_data = {
                    "id": i,
                    "text": chunk,
                    "embedding": embedding,
                    "hash": hashlib.md5(chunk.encode()).hexdigest()
                }
                embeddings_data["chunks"].append(chunk_data)
            else:
                print(f"Failed to get embedding for chunk {i+1}")
        
        return embeddings_data
    
    def save_embeddings(self, embeddings_data: Dict[str, Any], output_file: Path):
        """Save embeddings to JSON file."""
        print(f"Saving embeddings to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2)
        print(f"Embeddings saved successfully!")

    def get_supported_files(self) -> List[Path]:
        """Get list of supported files from input directory."""
        # Common text file extensions
        supported_extensions = {'.txt', '.md', '.rst', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'}
        
        files = []
        if self.input_dir.exists():
            for file_path in self.input_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)
        
        return files

    def process_all_files(self):
        """Process all files in the input directory."""
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all supported files
        files_to_process = self.get_supported_files()
        
        if not files_to_process:
            print(f"No supported files found in {self.input_dir}")
            print("Supported extensions: .txt, .md, .rst, .py, .js, .html, .css, .json, .xml, .csv, .log")
            return
        
        print(f"Found {len(files_to_process)} files to process")
        
        successful_embeddings = 0
        failed_embeddings = 0
        
        for i, file_path in enumerate(files_to_process, 1):
            print(f"\n{'='*60}")
            print(f"Processing file {i}/{len(files_to_process)}: {file_path.name}")
            print(f"{'='*60}")
            
            try:
                # Generate output filename
                output_filename = f"{file_path.stem}_embeddings.json"
                output_path = self.output_dir / output_filename
                
                # Skip if embeddings already exist
                if output_path.exists():
                    print(f"Embeddings already exist for {file_path.name}, skipping...")
                    continue
                
                # Process document
                embeddings_data = self.embed_document(file_path)
                self.save_embeddings(embeddings_data, output_path)
                
                print(f"✓ Successfully processed {file_path.name}")
                print(f"  Output: {output_path}")
                print(f"  Total chunks: {embeddings_data['total_chunks']}")
                print(f"  Successful embeddings: {len(embeddings_data['chunks'])}")
                
                successful_embeddings += 1
                
            except Exception as e:
                print(f"✗ Error processing {file_path.name}: {e}")
                failed_embeddings += 1
        
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total files processed: {len(files_to_process)}")
        print(f"Successful embeddings: {successful_embeddings}")
        print(f"Failed embeddings: {failed_embeddings}")
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")

def main():
    try:
        embedder = DocumentEmbedder()
        
        # Check if input directory exists
        if not embedder.input_dir.exists():
            print(f"Error: Input directory {embedder.input_dir} does not exist")
            sys.exit(1)
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{embedder.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
        except:
            print("Error: Cannot connect to Ollama. Please ensure Ollama is running.")
            print("Start Ollama with: ollama serve")
            sys.exit(1)
        
        # Check if embedding model is available
        try:
            test_embedding = embedder.get_embedding("test")
            if not test_embedding:
                print(f"Error: Cannot use embedding model '{embedder.embed_model}'")
                print(f"Please pull the model with: ollama pull {embedder.embed_model}")
                sys.exit(1)
        except:
            print(f"Error: Embedding model '{embedder.embed_model}' not available")
            print(f"Please pull the model with: ollama pull {embedder.embed_model}")
            sys.exit(1)
        
        # Process all files
        embedder.process_all_files()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()