import json
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

class MemoryManager:
    """Handles all memory storage, retrieval, and embedding operations for the AI assistant"""
    
    def __init__(self, project_root: Path, ollama_endpoint: str, embed_model: str, 
                 botname: str, username: str, max_context_entries: int = 50):
        self.project_root = project_root
        self.ollama_endpoint = ollama_endpoint
        self.embed_model = embed_model
        self.botname = botname
        self.username = username
        self.max_context_entries = max_context_entries
        
        # Memory file paths
        self.memory_file = project_root / "personality" / "memory" / "memory.json"
        self.embeddings_file = project_root / "personality" / "memory" / "embeddings.json"
        
        # Memory storage
        self.memory = []  # List of conversation entries
        self.embeddings_data = []  # List of embedded summaries
        
        # Terminal colors
        self.system_color = "\033[95m"
        self.error_color = "\033[91m"
        self.reset_color = "\033[0m"
        
        # Initialize memory system
        self._init_embeddings()
        self._load_memory()
    
    def _init_embeddings(self):
        """Test Ollama embedding model availability"""
        try:
            # Test if the embedding model is available
            test_response = self._get_ollama_embedding("test")
            if test_response is not None:
                print(f"{self.system_color}[Embeddings] Loaded {self.embed_model} model.{self.reset_color}")
            else:
                print(f"{self.error_color}[Error] Failed embed model init: {self.embed_model}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed test: {e}{self.reset_color}")

    def _get_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Ollama API"""
        try:
            url = f"{self.ollama_endpoint}/api/embeddings"
            payload = {
                "model": self.embed_model,
                "prompt": text
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("embedding")
            
            if embedding is None:
                print(f"{self.error_color}[Error] No embedding return: {text[:50]}...{self.reset_color}")
                return None
                
            return embedding
            
        except requests.exceptions.RequestException as e:
            print(f"{self.error_color}[Error] Ollama embed API req fail: {e}{self.reset_color}")
            return None
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to get embed: {e}{self.reset_color}")
            return None

    def _load_memory(self):
        """Load memory from JSON file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                print(f"{self.system_color}[Memory] Loaded {len(self.memory)} entries.{self.reset_color}")
            else:
                self.memory = []
                self._save_memory()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to load mem: {e}{self.reset_color}")
            self.memory = []
            
        # Load embeddings
        try:
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    self.embeddings_data = json.load(f)
                print(f"{self.system_color}[Embeddings] Loaded {len(self.embeddings_data)} embed.{self.reset_color}")
            else:
                self.embeddings_data = []
                self._save_embeddings()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed load: {e}{self.reset_color}")
            self.embeddings_data = []

    def _save_memory(self):
        """Save memory to JSON file"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            print(f"{self.system_color}[Memory] Saved {len(self.memory)} entries to file.{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed mem save: {e}{self.reset_color}")

    def _save_embeddings(self):
        """Save embeddings to JSON file"""
        try:
            self.embeddings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.embeddings_file, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed save: {e}{self.reset_color}")

    def _parse_human_datetime(self, timestamp_str: str) -> datetime:
        """Parse human-readable timestamp to datetime object"""
        try:
            # Try multiple formats
            formats = [
                "%A, %B %d, %Y at %I:%M %p UTC",
                "%A, %B %d, %Y at %H:%M UTC",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            # If no format works, try parsing ISO format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except Exception:
            # Fallback to current time
            return datetime.now(timezone.utc)

    def _format_timestamp(self, dt: Optional[datetime] = None) -> str:
        """Format datetime to human-readable string"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")

    def add_embedding(self, text: str, metadata: Dict[str, Any] = {}):
        """Add text to embeddings with metadata using Ollama"""
        if not text.strip():
            return
            
        try:
            embedding = self._get_ollama_embedding(text)
            if embedding is None:
                print(f"{self.error_color}[Error] Failed to get embedding for text: {text[:50]}...{self.reset_color}")
                return
                
            self.embeddings_data.append({
                'text': text,
                'embedding': embedding,
                'metadata': metadata or {},
                'timestamp': self._format_timestamp()
            })
            self._save_embeddings()
            print(f"{self.system_color}[Embeddings] Added embedding for: {text[:50]}...{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to create embedding: {e}{self.reset_color}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays for easier calculation
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return dot_product / (norm_a * norm_b)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to calculate similarity: {e}{self.reset_color}")
            return 0.0

    def search_embeddings(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search embeddings for similar content using Ollama"""
        if not self.embeddings_data:
            return []
            
        try:
            query_embedding = self._get_ollama_embedding(query)
            if query_embedding is None:
                print(f"{self.error_color}[Error] Failed to get query embedding{self.reset_color}")
                return []
            
            results = []
            for item in self.embeddings_data:
                embedding = item.get('embedding')
                if not embedding:
                    continue
                    
                similarity = self._cosine_similarity(query_embedding, embedding)
                results.append({
                    'text': item['text'],
                    'similarity': float(similarity),
                    'metadata': item.get('metadata', {}),
                    'timestamp': item.get('timestamp', '')
                })
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to search embeddings: {e}{self.reset_color}")
            return []

    def get_recent_context(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Get recent conversation entries for context"""
        if limit == 0:
            limit = self.max_context_entries
        
        # Get recent raw entries
        recent_entries = self.memory[-limit:] if len(self.memory) > limit else self.memory
        return recent_entries

    def get_memory_context(self, query: str) -> str:
        """Get relevant memory context from embeddings and recent conversations"""
        context_parts = []
        
        # Get embedded summaries
        similar_memories = self.search_embeddings(query, k=3)
        if similar_memories:
            context_parts.append("=== RELEVANT MEMORIES ===")
            for memory in similar_memories:
                context_parts.append(f"- {memory['text']} (similarity: {memory['similarity']:.2f})")
            context_parts.append("")
        
        # Get recent conversations
        recent = self.get_recent_context()
        if recent:
            context_parts.append("=== RECENT CONVERSATIONS ===")
            for entry in recent:
                role = entry.get('role', '')
                content = entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                
                if role == 'user':
                    context_parts.append(f"[{timestamp}] {self.username}: {content}")
                elif role == 'assistant':
                    context_parts.append(f"[{timestamp}] {self.botname}: {content}")
            context_parts.append("")
        
        return "\n".join(context_parts)

    def save_interaction(self, user_input: str, bot_response: str):
        """Save user input and bot response to memory"""
        timestamp = self._format_timestamp()
        
        # Add user message
        self.memory.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Add assistant response
        self.memory.append({
            "role": "assistant", 
            "content": bot_response,
            "timestamp": timestamp
        })
        
        self._save_memory()
        print(f"{self.system_color}[Memory] Saved interaction to memory.json{self.reset_color}")

    def print_long_term_memory(self):
        """Print memory statistics and recent entries"""
        print(f"[Memory] Total entries: {len(self.memory)}")
        print(f"[Memory] Total embeddings: {len(self.embeddings_data)}")
        
        if self.memory:
            print("\n=== RECENT MEMORY ===")
            recent = self.memory[-10:] if len(self.memory) > 10 else self.memory
            for entry in recent:
                role = entry.get('role', '')
                content = entry.get('content', '')[:100] + "..." if len(entry.get('content', '')) > 100 else entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                print(f"[{timestamp}] {role}: {content}")
        
        if self.embeddings_data:
            print("\n=== EMBEDDED SUMMARIES ===")
            for emb in self.embeddings_data[-5:]:  # Show last 5 summaries
                text = emb.get('text', '')[:100] + "..." if len(emb.get('text', '')) > 100 else emb.get('text', '')
                timestamp = emb.get('timestamp', '')
                print(f"[{timestamp}] {text}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Return memory statistics for bot info"""
        return {
            'memory_entries': len(self.memory),
            'embeddings_count': len(self.embeddings_data)
        }

    def clear_memory(self):
        """Clear all memory and embeddings"""
        self.memory = []
        self.embeddings_data = []
        self._save_memory()
        self._save_embeddings()
        print(f"{self.system_color}[Memory] All memory cleared.{self.reset_color}")

    def export_memory(self, filepath: str):
        """Export memory to a specified file"""
        try:
            export_data = {
                'memory': self.memory,
                'embeddings': self.embeddings_data,
                'export_timestamp': self._format_timestamp()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"{self.system_color}[Memory] Exported to {filepath}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to export memory: {e}{self.reset_color}")

    def import_memory(self, filepath: str):
        """Import memory from a specified file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'memory' in import_data:
                self.memory.extend(import_data['memory'])
            
            if 'embeddings' in import_data:
                self.embeddings_data.extend(import_data['embeddings'])
            
            self._save_memory()
            self._save_embeddings()
            
            print(f"{self.system_color}[Memory] Imported from {filepath}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to import memory: {e}{self.reset_color}")