# Filename: BASE/memory_methods/memory_manipulation.py
import json
import requests
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import glob

from personality.controls import MEMORY_LENGTH

class MemoryManager:
    """Memory manager for structured embeddings and conversation history"""
    
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
        self.base_memory_dir = project_root / "personality" / "memory_base" / "base_memory"
        
        # Memory storage
        self.memory = []  # List of conversation entries (current day + unsummarized entries only)
        self.embeddings_data = []  # List of embedded summaries only (past days)
        self.base_embeddings = []  # List of base knowledge embeddings
        
        # Terminal colors
        self.system_color = "\033[95m"
        self.error_color = "\033[91m"
        self.info_color = "\033[94m"
        self.success_color = "\033[92m"
        self.reset_color = "\033[0m"
        
        # Initialize memory system
        self._init_embeddings()
        self._load_memory()
        self._load_base_memory()
    
    def _init_embeddings(self):
        """Test Ollama embedding model availability"""
        try:
            test_response = self._get_ollama_embedding("test")
            if test_response is not None:
                print(f"{self.success_color}[Embeddings] Loaded {self.embed_model} model.{self.reset_color}")
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
        """Load memory from JSON file - current day entries and unsummarized entries only"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                print(f"{self.system_color}[Memory] Loaded {len(self.memory)} current/unsummarized entries.{self.reset_color}")
            else:
                self.memory = []
                self._save_memory()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to load mem: {e}{self.reset_color}")
            self.memory = []
            
        # Load embeddings (these are daily summaries only)
        try:
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    self.embeddings_data = json.load(f)
                print(f"{self.system_color}[Embeddings] Loaded {len(self.embeddings_data)} daily summaries.{self.reset_color}")
            else:
                self.embeddings_data = []
                self._save_embeddings()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed load: {e}{self.reset_color}")
            self.embeddings_data = []

    def _load_base_memory(self):
        """Load base memory embeddings with validation"""
        self.base_embeddings = []
        
        try:
            if not self.base_memory_dir.exists():
                print(f"{self.info_color}[Base Memory] Directory not found: {self.base_memory_dir}{self.reset_color}")
                return
                
            # Find all JSON files in the base_memory directory
            json_files = list(self.base_memory_dir.glob("*.json"))
            
            if not json_files:
                print(f"{self.info_color}[Base Memory] No JSON files found in {self.base_memory_dir}{self.reset_color}")
                return
            
            total_loaded = 0
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    # Handle different embedding file structures
                    embeddings_to_load = []
                    
                    if isinstance(file_data, dict) and 'embeddings' in file_data:
                        embeddings_to_load = file_data['embeddings']
                        processing_method = file_data.get('processing_method', 'unknown')
                        print(f"{self.info_color}[Base Memory] Found {processing_method} processed file: {json_file.name}{self.reset_color}")
                    elif isinstance(file_data, list):
                        embeddings_to_load = file_data
                    elif isinstance(file_data, dict):
                        if 'data' in file_data:
                            embeddings_to_load = file_data['data']
                        else:
                            embeddings_to_load = [file_data]
                    
                    # Validate and add embeddings
                    file_count = 0
                    for item in embeddings_to_load:
                        if self._validate_embedding_item(item):
                            # Add source metadata
                            metadata = item.get('metadata', {})
                            metadata['source_file'] = json_file.name
                            metadata['source_type'] = 'base_memory'
                            item['metadata'] = metadata
                            
                            self.base_embeddings.append(item)
                            file_count += 1
                        else:
                            print(f"{self.error_color}[Base Memory] Invalid embedding in {json_file.name}{self.reset_color}")
                    
                    total_loaded += file_count
                    print(f"{self.success_color}[Base Memory] Loaded {file_count} embeddings from {json_file.name}{self.reset_color}")
                    
                except Exception as e:
                    print(f"{self.error_color}[Error] Failed to load base memory file {json_file.name}: {e}{self.reset_color}")
            
            print(f"{self.success_color}[Base Memory] Total loaded: {total_loaded} embeddings from {len(json_files)} files{self.reset_color}")
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to load base memory: {e}{self.reset_color}")

    def _validate_embedding_item(self, item: Dict[str, Any]) -> bool:
        """Validate embedding item structure"""
        required_fields = ['text', 'embedding']
        return (
            isinstance(item, dict) and
            all(field in item for field in required_fields) and
            isinstance(item['text'], str) and
            len(item['text'].strip()) > 0 and
            isinstance(item['embedding'], list) and
            len(item['embedding']) > 0
        )

    def _save_memory(self):
        """Save current day entries and unsummarized entries to JSON file"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed mem save: {e}{self.reset_color}")

    def _save_embeddings(self):
        """Save embedded daily summaries to JSON file"""
        try:
            self.embeddings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.embeddings_file, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed save: {e}{self.reset_color}")

    def _parse_human_datetime(self, timestamp_str: str) -> datetime:
        """Parse human-readable timestamp to datetime object"""
        try:
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
            
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except Exception:
            return datetime.now(timezone.utc)

    def _format_timestamp(self, dt: Optional[datetime] = None) -> str:
        """Format datetime to human-readable string"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")

    def get_past_day_entries_for_summarization(self) -> List[Dict[str, Any]]:
        """Get entries from past days only (not current day) for summarization"""
        past_day_entries = []
        today = datetime.now(timezone.utc).date()
        
        for entry in self.memory:
            try:
                timestamp_str = entry.get('timestamp', '')
                entry_datetime = self._parse_human_datetime(timestamp_str)
                entry_date = entry_datetime.date()
                
                # Only include entries from past days
                if entry_date < today:
                    past_day_entries.append(entry)
            except Exception as e:
                print(f"{self.error_color}[Error] Failed to parse entry timestamp: {e}{self.reset_color}")
                continue
        
        return past_day_entries

    def get_current_day_entries(self) -> List[Dict[str, Any]]:
        """Get entries from current day only"""
        current_day_entries = []
        today = datetime.now(timezone.utc).date()
        
        for entry in self.memory:
            try:
                timestamp_str = entry.get('timestamp', '')
                entry_datetime = self._parse_human_datetime(timestamp_str)
                entry_date = entry_datetime.date()
                
                # Only include entries from current day
                if entry_date >= today:
                    current_day_entries.append(entry)
            except Exception as e:
                print(f"{self.error_color}[Error] Failed to parse entry timestamp: {e}{self.reset_color}")
                continue
        
        return current_day_entries

    def remove_summarized_past_day_entries(self, num_entries_to_remove: int):
        """Remove past day entries that have been summarized, keep current day entries"""
        if num_entries_to_remove <= 0:
            return
        
        original_count = len(self.memory)
        current_day_entries = self.get_current_day_entries()
        
        # Keep only current day entries
        self.memory = current_day_entries
        
        self._save_memory()
        removed_count = original_count - len(self.memory)
        print(f"{self.system_color}[Memory] Removed {removed_count} summarized past day entries, kept {len(self.memory)} current day entries{self.reset_color}")

    def add_summary_embedding(self, summary_text: str, metadata: Dict[str, Any] = {}):
        """Add a daily summary text to embeddings (used by summarizer only)"""
        if not summary_text.strip():
            return
            
        try:
            embedding = self._get_ollama_embedding(summary_text)
            if embedding is None:
                print(f"{self.error_color}[Error] Failed to get embedding for summary: {summary_text[:50]}...{self.reset_color}")
                return
            
            # Mark this as a daily summary embedding
            summary_metadata = metadata.copy()
            summary_metadata['entry_type'] = summary_metadata.get('entry_type', 'daily_summary')
            summary_metadata['created_by'] = 'summarizer'
                
            self.embeddings_data.append({
                'text': summary_text,
                'embedding': embedding,
                'metadata': summary_metadata,
                'timestamp': self._format_timestamp()
            })
            self._save_embeddings()
            print(f"{self.system_color}[Embeddings] Added daily summary embedding: {summary_text[:50]}...{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to create summary embedding: {e}{self.reset_color}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return dot_product / (norm_a * norm_b)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to calculate similarity: {e}{self.reset_color}")
            return 0.0

    def search_embeddings(self, query: str, k: int = 5, include_base: bool = True) -> List[Dict[str, Any]]:
        """Search embeddings with similarity scoring"""
        all_embeddings = self.embeddings_data.copy()  # These are daily summaries
        if include_base:
            all_embeddings.extend(self.base_embeddings)  # These are base knowledge
        
        if not all_embeddings:
            return []
            
        try:
            query_embedding = self._get_ollama_embedding(query)
            if query_embedding is None:
                print(f"{self.error_color}[Error] Failed to get query embedding{self.reset_color}")
                return []
            
            results = []
            
            for item in all_embeddings:
                embedding = item.get('embedding')
                if not embedding:
                    continue
                    
                similarity = self._cosine_similarity(query_embedding, embedding)
                
                metadata = item.get('metadata', {})
                source_type = metadata.get('source_type', 'personal')
                
                results.append({
                    'text': item['text'],
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'timestamp': item.get('timestamp', ''),
                    'source_type': source_type
                })
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Filter for minimum similarity threshold
            filtered_results = [r for r in results if r['similarity'] > 0.3]
            
            return filtered_results[:k]
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to search embeddings: {e}{self.reset_color}")
            return []

    def search_base_memory_only(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search only base memory embeddings"""
        if not self.base_embeddings:
            return []
            
        try:
            query_embedding = self._get_ollama_embedding(query)
            if query_embedding is None:
                return []
            
            results = []
            for item in self.base_embeddings:
                embedding = item.get('embedding')
                if not embedding:
                    continue
                    
                similarity = self._cosine_similarity(query_embedding, embedding)
                
                metadata = item.get('metadata', {})
                
                results.append({
                    'text': item['text'],
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'timestamp': item.get('timestamp', ''),
                    'source_type': 'base_memory'
                })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to search base memory: {e}{self.reset_color}")
            return []

    def get_memory_context_with_search(self, query: str, include_base: bool = True) -> str:
        """Force inclusion of long-term memory search regardless of query content"""
        return self.get_memory_context(query, include_base=include_base, force_long_term=True)

    def get_short_term_context_only(self) -> str:
        """Get only current day conversation context without any long-term memory"""
        context_parts = []
        
        recent = self.get_current_day_context()
        if recent:
            context_parts.append("=== TODAY'S CONVERSATIONS ===")
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

    def get_current_day_context(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Get current day conversation entries for context"""
        if limit == 0:
            limit = self.max_context_entries
        
        current_day_entries = self.get_current_day_entries()
        recent_entries = current_day_entries[-limit:] if len(current_day_entries) > limit else current_day_entries
        return recent_entries

    def get_recent_context(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Get recent conversation entries for context (current day + some recent unsummarized)"""
        if limit == 0:
            limit = self.max_context_entries
        
        recent_entries = self.memory[-limit:] if len(self.memory) > limit else self.memory
        return recent_entries

    def get_memory_context(self, query: str, include_base: bool = True, force_long_term: bool = False) -> str:
        """Get memory context with search results and recent conversations"""
        context_parts = []
        
        # Long-term memory search (daily summaries + base knowledge)
        if force_long_term:
            similar_memories = self.search_embeddings(query, k=5, include_base=include_base)
            
            if similar_memories:
                context_parts.append("=== RELEVANT KNOWLEDGE ===")
                
                # Group by source type
                base_memories = [m for m in similar_memories if m['source_type'] == 'base_memory']
                daily_summaries = [m for m in similar_memories if m['source_type'] == 'personal']
                
                if base_memories:
                    context_parts.append("Knowledge Base:")
                    for memory in base_memories[:3]:  # Limit base knowledge
                        context_parts.append(f"- {memory['text']} (similarity: {memory['similarity']:.2f})")
                
                if daily_summaries:
                    context_parts.append("Past Days' Summaries:")
                    for memory in daily_summaries[:3]:  # Limit daily summaries
                        date = memory.get('metadata', {}).get('conversation_date', 'unknown date')
                        context_parts.append(f"- [{date}] {memory['text']} (similarity: {memory['similarity']:.2f})")
                
                context_parts.append("")
                print(f"{self.info_color}[Memory] Retrieved knowledge context{self.reset_color}")
        
        # Always include current day conversations (from individual chat entries)
        recent = self.get_current_day_context()
        if recent:
            context_parts.append("=== TODAY'S CONVERSATIONS ===")
            for entry in recent[-MEMORY_LENGTH:]:
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
        """Save user input and bot response to memory as individual entries (not embedded)"""
        timestamp = self._format_timestamp()
        
        # Save as individual chat entries - these are NOT embedded
        self.memory.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        self.memory.append({
            "role": "assistant", 
            "content": bot_response,
            "timestamp": timestamp
        })
        
        self._save_memory()
        print(f"{self.system_color}[Memory] Saved today's interaction to memory.json (not embedded){self.reset_color}")

    def get_entries_for_summarization(self, start_index: int = 0) -> List[Dict[str, Any]]:
        """Get memory entries for summarization starting from a specific index (deprecated - use get_past_day_entries_for_summarization)"""
        return self.memory[start_index:]

    def mark_entries_as_summarized(self, end_index: int):
        """Remove entries that have been summarized to prevent re-processing (deprecated - use remove_summarized_past_day_entries)"""
        if end_index < len(self.memory):
            # Keep recent entries, remove older ones that were summarized
            self.memory = self.memory[end_index:]
            self._save_memory()
            print(f"{self.system_color}[Memory] Archived {end_index} summarized entries{self.reset_color}")

    def print_long_term_memory(self):
        """Display memory statistics and recent entries"""
        current_day_count = len(self.get_current_day_entries())
        past_day_count = len(self.get_past_day_entries_for_summarization())
        
        print(f"[Memory] Current day entries: {current_day_count}")
        print(f"[Memory] Past day unsummarized entries: {past_day_count}")
        print(f"[Memory] Total chat entries: {len(self.memory)}")
        print(f"[Memory] Total daily summary embeddings: {len(self.embeddings_data)}")
        print(f"[Memory] Total base embeddings: {len(self.base_embeddings)}")
        
        # Base memory breakdown
        if self.base_embeddings:
            source_files = {}
            for emb in self.base_embeddings:
                metadata = emb.get('metadata', {})
                source_file = metadata.get('source_file', 'unknown')
                source_files[source_file] = source_files.get(source_file, 0) + 1
            
            print(f"\n=== BASE KNOWLEDGE BREAKDOWN ===")
            print("Source Files:")
            for source_file, count in sorted(source_files.items()):
                print(f"  - {source_file}: {count}")
        
        # Daily summaries breakdown
        if self.embeddings_data:
            print(f"\n=== DAILY SUMMARIES BREAKDOWN ===")
            summary_dates = {}
            for emb in self.embeddings_data:
                metadata = emb.get('metadata', {})
                date = metadata.get('conversation_date', 'unknown date')
                summary_dates[date] = summary_dates.get(date, 0) + 1
            
            print("Summarized Days:")
            for date, count in sorted(summary_dates.items()):
                print(f"  - {date}: {count} summaries")
        
        if self.memory:
            print(f"\n=== RECENT CHAT ENTRIES ===")
            recent = self.memory[-10:] if len(self.memory) > 10 else self.memory
            for entry in recent:
                role = entry.get('role', '')
                content = entry.get('content', '')[:100] + "..." if len(entry.get('content', '')) > 100 else entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                
                # Show if entry is from today or past day
                try:
                    entry_datetime = self._parse_human_datetime(timestamp)
                    entry_date = entry_datetime.date()
                    today = datetime.now(timezone.utc).date()
                    day_marker = "[TODAY]" if entry_date >= today else "[PAST]"
                except:
                    day_marker = "[?]"
                
                print(f"{day_marker} [{timestamp}] {role}: {content}")

    def reload_base_memory(self):
        """Reload base memory embeddings from files"""
        print(f"{self.info_color}[Base Memory] Reloading base memory files...{self.reset_color}")
        self._load_base_memory()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        current_day_count = len(self.get_current_day_entries())
        past_day_count = len(self.get_past_day_entries_for_summarization())
        
        return {
            'current_day_entries': current_day_count,
            'past_day_unsummarized_entries': past_day_count,
            'total_memory_entries': len(self.memory),
            'daily_summary_embeddings_count': len(self.embeddings_data),
            'base_embeddings_count': len(self.base_embeddings)
        }

    def clear_memory(self):
        """Clear all personal memory and embeddings (does not affect base memory)"""
        self.memory = []
        self.embeddings_data = []
        self._save_memory()
        self._save_embeddings()
        print(f"{self.success_color}[Memory] Personal memory cleared. Base memory preserved.{self.reset_color}")

    def export_memory(self, filepath: str):
        """Export memory to a specified file"""
        try:
            export_data = {
                'chat_entries': self.memory,
                'daily_summary_embeddings': self.embeddings_data,
                'base_embeddings_count': len(self.base_embeddings),
                'current_day_entries': len(self.get_current_day_entries()),
                'past_day_entries': len(self.get_past_day_entries_for_summarization()),
                'export_timestamp': self._format_timestamp()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"{self.success_color}[Memory] Exported to {filepath}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to export memory: {e}{self.reset_color}")

    def import_memory(self, filepath: str):
        """Import memory from a specified file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'chat_entries' in import_data:
                self.memory.extend(import_data['chat_entries'])
            elif 'memory' in import_data:  # Legacy format
                self.memory.extend(import_data['memory'])
            
            if 'daily_summary_embeddings' in import_data:
                self.embeddings_data.extend(import_data['daily_summary_embeddings'])
            elif 'summary_embeddings' in import_data:  # Legacy format
                self.embeddings_data.extend(import_data['summary_embeddings'])
            elif 'embeddings' in import_data:  # Legacy format
                self.embeddings_data.extend(import_data['embeddings'])
            
            self._save_memory()
            self._save_embeddings()
            
            print(f"{self.success_color}[Memory] Imported from {filepath}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to import memory: {e}{self.reset_color}")

    def debug_search_results(self, query: str, k: int = 5) -> None:
        """Debug method to see detailed search results"""
        print(f"{self.info_color}[Debug] Searching for: '{query}'{self.reset_color}")
        
        results = self.search_embeddings(query, k=k, include_base=True)
        
        print(f"{self.info_color}[Debug] Found {len(results)} results:{self.reset_color}")
        for i, result in enumerate(results):
            metadata = result.get('metadata', {})
            source_type = result.get('source_type', 'unknown')
            
            print(f"\n{self.info_color}[Result {i+1}]{self.reset_color}")
            print(f"  Similarity: {result['similarity']:.3f}")
            print(f"  Source: {source_type}")
            
            if source_type == 'personal':
                date = metadata.get('conversation_date', 'unknown date')
                print(f"  Date: {date}")
            elif source_type == 'base_memory':
                source_file = metadata.get('source_file', 'unknown file')
                print(f"  File: {source_file}")
                
            print(f"  Text: {result['text'][:150]}...")

    def get_summarization_candidate_days(self) -> List[str]:
        """Get list of past days that have entries available for summarization"""
        past_day_entries = self.get_past_day_entries_for_summarization()
        
        if not past_day_entries:
            return []
        
        # Group by day to see which days have enough entries
        daily_groups = {}
        today = datetime.now(timezone.utc).date()
        
        for entry in past_day_entries:
            try:
                timestamp_str = entry.get('timestamp', '')
                entry_datetime = self._parse_human_datetime(timestamp_str)
                entry_date = entry_datetime.date()
                
                if entry_date < today:  # Only past days
                    date_str = entry_date.strftime('%Y-%m-%d')
                    if date_str not in daily_groups:
                        daily_groups[date_str] = []
                    daily_groups[date_str].append(entry)
            except Exception:
                continue
        
        # Return only days with sufficient entries for meaningful summarization
        candidate_days = [date for date, entries in daily_groups.items() if len(entries) >= 4]
        return sorted(candidate_days)