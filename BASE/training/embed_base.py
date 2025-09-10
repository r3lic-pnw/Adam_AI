import os
import json
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import requests
from datetime import datetime

class MarkdownChunker:
    """Handles intelligent chunking of markdown documents with section awareness."""
    
    def __init__(self, chunk_size: int = 1200, overlap: int = 150, min_chunk_size: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract markdown sections with their hierarchy."""
        sections = []
        lines = text.split('\n')
        current_section = {'level': 0, 'title': '', 'content': [], 'start_line': 0}
        
        for i, line in enumerate(lines):
            # Check for markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            
            if header_match:
                # Save previous section if it has content
                if current_section['content'] or current_section['title']:
                    current_section['content_text'] = '\n'.join(current_section['content']).strip()
                    current_section['end_line'] = i - 1
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    'level': level,
                    'title': title,
                    'content': [],
                    'start_line': i,
                    'header_line': line
                }
            else:
                current_section['content'].append(line)
        
        # Don't forget the last section
        if current_section['content'] or current_section['title']:
            current_section['content_text'] = '\n'.join(current_section['content']).strip()
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _get_section_context(self, sections: List[Dict[str, Any]], index: int) -> str:
        """Build hierarchical context for a section."""
        section = sections[index]
        context_parts = []
        
        # Add higher-level headers for context
        current_level = section['level']
        for i in range(index - 1, -1, -1):
            prev_section = sections[i]
            if prev_section['level'] < current_level:
                context_parts.insert(0, prev_section['title'])
                current_level = prev_section['level']
                if current_level <= 1:  # Stop at main section
                    break
        
        return ' > '.join(context_parts) if context_parts else ''
    
    def _should_merge_sections(self, section1: Dict[str, Any], section2: Dict[str, Any]) -> bool:
        """Determine if two sections should be merged into one chunk."""
        combined_length = len(section1.get('content_text', '')) + len(section2.get('content_text', ''))
        
        # Always merge if combined is under chunk size
        if combined_length <= self.chunk_size:
            return True
        
        # Merge small sections with their parent
        if (section1.get('level', 0) < section2.get('level', 0) and 
            len(section2.get('content_text', '')) < self.min_chunk_size):
            return True
        
        return False
    
    def chunk_markdown(self, text: str) -> List[Dict[str, Any]]:
        """Intelligently chunk markdown text preserving section boundaries."""
        sections = self._extract_sections(text)
        chunks = []
        
        if not sections:
            # Fallback to basic chunking if no sections found
            return self._basic_chunk(text)
        
        i = 0
        while i < len(sections):
            section = sections[i]
            
            # Build chunk starting with current section
            chunk_parts = []
            chunk_sections = [i]
            
            # Add section header and content
            if section['title']:
                header_prefix = '#' * section['level']
                chunk_parts.append(f"{header_prefix} {section['title']}")
            
            if section.get('content_text'):
                chunk_parts.append(section['content_text'])
            
            current_length = len('\n'.join(chunk_parts))
            
            # Try to merge with following sections
            j = i + 1
            while j < len(sections) and current_length < self.chunk_size:
                next_section = sections[j]
                
                # Calculate potential new length
                next_content = []
                if next_section['title']:
                    header_prefix = '#' * next_section['level']
                    next_content.append(f"{header_prefix} {next_section['title']}")
                
                if next_section.get('content_text'):
                    next_content.append(next_section['content_text'])
                
                next_text = '\n'.join(next_content)
                potential_length = current_length + len('\n' + next_text)
                
                # Check if we should merge
                if (potential_length <= self.chunk_size or 
                    self._should_merge_sections(section, next_section)):
                    chunk_parts.append(next_text)
                    chunk_sections.append(j)
                    current_length = potential_length
                    j += 1
                else:
                    break
            
            # Create chunk metadata
            chunk_text = '\n'.join(chunk_parts).strip()
            if chunk_text:
                # Get hierarchical context
                context = self._get_section_context(sections, i)
                
                # Determine chunk type
                chunk_type = self._classify_chunk(chunk_text, section)
                
                chunk_data = {
                    'text': chunk_text,
                    'sections': chunk_sections,
                    'main_section_title': section['title'],
                    'section_level': section['level'],
                    'context_path': context,
                    'chunk_type': chunk_type,
                    'char_count': len(chunk_text),
                    'keywords': self._extract_keywords(chunk_text)
                }
                chunks.append(chunk_data)
            
            # Move to next unprocessed section
            i = max(j, i + 1)
        
        return chunks
    
    def _classify_chunk(self, text: str, section: Dict[str, Any]) -> str:
        """Classify the type of content in the chunk."""
        title = section.get('title', '').lower()
        text_lower = text.lower()
        
        # Classification based on content patterns
        if any(word in title for word in ['recipe', 'craft', 'smelt']):
            return 'recipe'
        elif any(word in title for word in ['combat', 'mob', 'fight', 'defense']):
            return 'combat'
        elif any(word in title for word in ['mining', 'ore', 'cave']):
            return 'mining'
        elif any(word in title for word in ['build', 'construct', 'shelter']):
            return 'building'
        elif any(word in title for word in ['farm', 'food', 'crop']):
            return 'farming'
        elif 'decision' in title or 'when to' in text_lower:
            return 'decision_guide'
        elif any(word in title for word in ['basic', 'fundamental', 'essential']):
            return 'fundamentals'
        elif re.search(r'\d+\.\s|\*\s|-\s', text):  # Lists
            return 'reference_list'
        else:
            return 'general_guide'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from chunk text for better retrieval."""
        # Common Minecraft terms for better semantic matching
        minecraft_terms = {
            'pick', 'axe', 'shovel', 'sword', 'armor', 'helmet', 'chest', 'boots',
            'wood', 'stone', 'iron', 'diamond', 'gold', 'coal', 'ore', 'ingot',
            'craft', 'smelt', 'furnace', 'table', 'recipe', 'build', 'block',
            'mob', 'zombie', 'skeleton', 'creeper', 'spider', 'enderman',
            'mine', 'dig', 'cave', 'surface', 'underground', 'lava', 'water',
            'food', 'hunger', 'health', 'damage', 'farm', 'crop', 'wheat',
            'torch', 'light', 'spawn', 'bed', 'sleep', 'day', 'night'
        }
        
        # Extract words and filter for relevance
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = []
        
        for word in set(words):
            # Include Minecraft-specific terms
            if word in minecraft_terms:
                keywords.append(word)
            # Include capitalized words (likely important terms)
            elif any(c.isupper() for c in text if word in text):
                keywords.append(word)
        
        return keywords[:10]  # Limit to most relevant
    
    def _basic_chunk(self, text: str) -> List[Dict[str, Any]]:
        """Fallback basic chunking for non-markdown text."""
        if len(text) <= self.chunk_size:
            return [{
                'text': text,
                'sections': [0],
                'main_section_title': 'Full Document',
                'section_level': 1,
                'context_path': '',
                'chunk_type': 'general_guide',
                'char_count': len(text),
                'keywords': self._extract_keywords(text)
            }]
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                sentence_break = text.rfind('.', start, end)
                if sentence_break > start + self.chunk_size // 2:
                    end = sentence_break + 1
                else:
                    word_break = text.rfind(' ', start, end)
                    if word_break > start + self.chunk_size // 2:
                        end = word_break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'sections': [chunk_id],
                    'main_section_title': f'Chunk {chunk_id + 1}',
                    'section_level': 1,
                    'context_path': '',
                    'chunk_type': 'general_guide',
                    'char_count': len(chunk_text),
                    'keywords': self._extract_keywords(chunk_text)
                })
                chunk_id += 1
            
            start = end - self.overlap
            if start >= len(text):
                break
        
        return chunks

class OllamaEmbedder:
    """Enhanced embedder with better error handling and retry logic."""
    
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.embed_url = f"{base_url}/api/embeddings"
        self.max_retries = 3
    
    def embed_text(self, text: str, context: str = "") -> List[float]:
        """Generate embedding for text with optional context."""
        # Prepend context for better semantic understanding
        full_text = f"{context}\n\n{text}" if context else text
        
        payload = {
            "model": self.model,
            "prompt": full_text
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.embed_url, json=payload, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                embedding = result.get("embedding", [])
                
                if embedding:
                    return embedding
                else:
                    print(f"    Empty embedding returned (attempt {attempt + 1})")
                    
            except requests.exceptions.RequestException as e:
                print(f"    Error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    print(f"    Failed after {self.max_retries} attempts")
                    return []
        
        return []
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for markdown chunks with enhanced metadata."""
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            print(f"  Processing chunk {i + 1}/{len(chunks)}: {chunk.get('main_section_title', 'Unnamed')[:50]}...")
            
            # Use context path for better embeddings
            context = f"Minecraft Guide - {chunk.get('context_path', '')}"
            embedding = self.embed_text(chunk['text'], context)
            
            if embedding:
                # Enhanced chunk data with all metadata
                chunk_data = {
                    "chunk_id": i,
                    "text": chunk['text'],
                    "embedding": embedding,
                    "embedding_dim": len(embedding),
                    "main_section_title": chunk.get('main_section_title', ''),
                    "section_level": chunk.get('section_level', 1),
                    "context_path": chunk.get('context_path', ''),
                    "chunk_type": chunk.get('chunk_type', 'general_guide'),
                    "char_count": chunk.get('char_count', 0),
                    "keywords": chunk.get('keywords', []),
                    "sections_included": chunk.get('sections', [])
                }
                embeddings.append(chunk_data)
            else:
                print(f"    Warning: Failed to generate embedding for chunk {i + 1}")
        
        return embeddings

class FileProcessor:
    """Enhanced processor optimized for structured documents."""
    
    def __init__(self, chunk_size: int = 1200, overlap: int = 150):
        self.chunker = MarkdownChunker(chunk_size, overlap)
        self.embedder = OllamaEmbedder()
    
    def process_file(self, file_path: Path, output_dir: Path) -> bool:
        """Process file with intelligent chunking and enhanced metadata."""
        try:
            print(f"Processing: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                print(f"  Warning: File {file_path.name} is empty, skipping.")
                return False
            
            # Intelligent chunking
            print("  Analyzing document structure and chunking...")
            chunks = self.chunker.chunk_markdown(text)
            print(f"  Created {len(chunks)} intelligent chunks")
            
            # Print chunk summary
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print("  Chunk distribution:")
            for chunk_type, count in chunk_types.items():
                print(f"    - {chunk_type}: {count}")
            
            # Generate embeddings
            print("  Generating embeddings with context...")
            embeddings = self.embedder.embed_chunks(chunks)
            
            if not embeddings:
                print(f"  Error: No embeddings generated for {file_path.name}")
                return False
            
            # Enhanced output data
            output_data = {
                "source_file": str(file_path),
                "processed_at": datetime.now().isoformat(),
                "total_chunks": len(chunks),
                "successful_embeddings": len(embeddings),
                "chunk_size": self.chunker.chunk_size,
                "overlap": self.chunker.overlap,
                "model": self.embedder.model,
                "chunk_types": chunk_types,
                "processing_method": "intelligent_markdown",
                "embeddings": embeddings
            }
            
            # Save enhanced embeddings
            output_file = output_dir / f"{file_path.stem}_embeddings.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Optimized pickle with compression
            pickle_file = output_dir / f"{file_path.stem}_embeddings.pkl"
            with open(pickle_file, 'wb') as f:
                pickle.dump(output_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            print(f"  ✅ Successfully processed {file_path.name}")
            print(f"  📄 JSON saved to: {output_file}")
            print(f"  📦 Pickle saved to: {pickle_file}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main processing function with enhanced reporting."""
    
    # Define paths
    input_dir = Path("./../../personality/memory_base/base_files")
    output_dir = Path("./../../personality/memory_base/base_memory")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all text files (including markdown)
    text_files = list(input_dir.glob("*.txt")) + list(input_dir.glob("*.md"))
    
    if not text_files:
        print(f"No .txt or .md files found in {input_dir}")
        return
    
    print(f"Found {len(text_files)} files to process")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    # Initialize processor with optimized settings for Minecraft guide
    processor = FileProcessor(chunk_size=1200, overlap=150)
    
    # Process files
    results = {"successful": 0, "failed": 0, "total_chunks": 0, "chunk_types": {}}
    
    for file_path in text_files:
        success = processor.process_file(file_path, output_dir)
        
        if success:
            results["successful"] += 1
            # Load chunk info for summary
            try:
                with open(output_dir / f"{file_path.stem}_embeddings.json", 'r') as f:
                    data = json.load(f)
                    results["total_chunks"] += data.get("total_chunks", 0)
                    chunk_types = data.get("chunk_types", {})
                    for chunk_type, count in chunk_types.items():
                        results["chunk_types"][chunk_type] = results["chunk_types"].get(chunk_type, 0) + count
            except:
                pass
        else:
            results["failed"] += 1
        
        print("-" * 30)
    
    # Enhanced summary
    print(f"\n📊 Processing Summary:")
    print(f"  Total files: {len(text_files)}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total chunks created: {results['total_chunks']}")
    
    if results['chunk_types']:
        print(f"\n📈 Chunk Type Distribution:")
        for chunk_type, count in sorted(results['chunk_types'].items()):
            print(f"  - {chunk_type}: {count}")
    
    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} files failed to process. Check the output above for details.")

def test_ollama_connection():
    """Enhanced connection test with model verification."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        print("🔍 Available Ollama models:")
        for name in model_names:
            print(f"  - {name}")
        
        if any("nomic-embed-text" in name for name in model_names):
            print("✅ nomic-embed-text model is available")
            
            # Test embedding generation
            embedder = OllamaEmbedder()
            test_embedding = embedder.embed_text("Test embedding generation")
            if test_embedding:
                print(f"✅ Embedding test successful (dimension: {len(test_embedding)})")
                return True
            else:
                print("❌ Embedding test failed")
                return False
        else:
            print("❌ nomic-embed-text model not found")
            print("   Run: ollama pull nomic-embed-text")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False

if __name__ == "__main__":
    print("🚀 Optimized Minecraft Guide Embedding System")
    print("=" * 60)
    
    # Test connection
    if test_ollama_connection():
        print("\n🔄 Starting intelligent document processing...")
        main()
    else:
        print("\n⚠️  Please ensure Ollama is running and nomic-embed-text model is installed.")
        print("   Commands:")
        print("   1. ollama serve")
        print("   2. ollama pull nomic-embed-text")