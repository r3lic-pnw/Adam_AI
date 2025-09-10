# Filename: BASE/memory_methods/memory_manipulation.py
import json
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import glob

from personality.controls import MEMORY_LENGTH

class MemoryManager:
    """Enhanced memory manager optimized for structured Minecraft guide embeddings"""
    
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
        self.memory = []  # List of conversation entries (individual user/assistant messages)
        self.embeddings_data = []  # List of embedded summaries only
        self.base_embeddings = []  # List of base knowledge embeddings
        
        # Enhanced categorization for Minecraft contexts
        self.minecraft_context_patterns = {
            'combat': ['fight', 'mob', 'attack', 'defend', 'weapon', 'armor', 'zombie', 'skeleton', 'creeper', 'spider', 'enderman'],
            'crafting': ['craft', 'recipe', 'make', 'build', 'create', 'furnace', 'table', 'smelt'],
            'mining': ['mine', 'dig', 'ore', 'cave', 'underground', 'pickaxe', 'stone', 'iron', 'diamond', 'coal'],
            'farming': ['farm', 'grow', 'crop', 'plant', 'food', 'wheat', 'carrot', 'potato', 'breed', 'animal'],
            'building': ['build', 'construct', 'house', 'shelter', 'wall', 'roof', 'door', 'block'],
            'survival': ['hunger', 'health', 'eat', 'sleep', 'bed', 'day', 'night', 'spawn'],
            'exploration': ['explore', 'travel', 'find', 'locate', 'biome', 'village', 'structure'],
            'progression': ['upgrade', 'advance', 'tier', 'better', 'improve', 'next', 'goal']
        }
        
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

    def _classify_query_intent(self, query: str) -> Tuple[str, float]:
        """Classify the query intent and return confidence score"""
        query_lower = query.lower()
        scores = {}
        
        for category, keywords in self.minecraft_context_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[category] = score / len(keywords)  # Normalize by category size
        
        if not scores:
            return 'general', 0.0
        
        best_category = max(scores, key=lambda k: scores[k])
        confidence = scores[best_category]
        
        return best_category, confidence

    def _load_memory(self):
        """Load memory from JSON file - these are individual chat entries, not embedded"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                print(f"{self.system_color}[Memory] Loaded {len(self.memory)} chat entries.{self.reset_color}")
            else:
                self.memory = []
                self._save_memory()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to load mem: {e}{self.reset_color}")
            self.memory = []
            
        # Load embeddings (these are summaries only)
        try:
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                    self.embeddings_data = json.load(f)
                print(f"{self.system_color}[Embeddings] Loaded {len(self.embeddings_data)} embedded summaries.{self.reset_color}")
            else:
                self.embeddings_data = []
                self._save_embeddings()
        except Exception as e:
            print(f"{self.error_color}[Error] Failed embed load: {e}{self.reset_color}")
            self.embeddings_data = []

    def _load_base_memory(self):
        """Enhanced base memory loading with better validation for structured embeddings"""
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
            chunk_type_counts = {}
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    # Handle enhanced embedding structure from our optimized system
                    embeddings_to_load = []
                    
                    if isinstance(file_data, dict) and 'embeddings' in file_data:
                        # This is the format from our enhanced embedding system
                        embeddings_to_load = file_data['embeddings']
                        processing_method = file_data.get('processing_method', 'unknown')
                        print(f"{self.info_color}[Base Memory] Found {processing_method} processed file: {json_file.name}{self.reset_color}")
                    elif isinstance(file_data, list):
                        # Direct list of embeddings
                        embeddings_to_load = file_data
                    elif isinstance(file_data, dict):
                        # Single embedding or other structure
                        if 'data' in file_data:
                            embeddings_to_load = file_data['data']
                        else:
                            embeddings_to_load = [file_data]
                    
                    # Validate and add embeddings with enhanced metadata
                    file_count = 0
                    for item in embeddings_to_load:
                        if self._validate_enhanced_embedding_item(item):
                            # Preserve enhanced metadata from our optimized chunking
                            enhanced_metadata = {
                                'source_file': json_file.name,
                                'source_type': 'base_memory',
                                # Preserve enhanced chunking metadata
                                'main_section_title': item.get('main_section_title', ''),
                                'section_level': item.get('section_level', 1),
                                'context_path': item.get('context_path', ''),
                                'chunk_type': item.get('chunk_type', 'general_guide'),
                                'char_count': item.get('char_count', 0),
                                'keywords': item.get('keywords', []),
                                'sections_included': item.get('sections_included', [])
                            }
                            
                            # Merge with existing metadata
                            if 'metadata' in item:
                                enhanced_metadata.update(item['metadata'])
                            item['metadata'] = enhanced_metadata
                            
                            # Track chunk types
                            chunk_type = enhanced_metadata.get('chunk_type', 'unknown')
                            chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1
                            
                            self.base_embeddings.append(item)
                            file_count += 1
                        else:
                            print(f"{self.error_color}[Base Memory] Invalid embedding in {json_file.name}{self.reset_color}")
                    
                    total_loaded += file_count
                    print(f"{self.success_color}[Base Memory] Loaded {file_count} embeddings from {json_file.name}{self.reset_color}")
                    
                except Exception as e:
                    print(f"{self.error_color}[Error] Failed to load base memory file {json_file.name}: {e}{self.reset_color}")
            
            print(f"{self.success_color}[Base Memory] Total loaded: {total_loaded} embeddings from {len(json_files)} files{self.reset_color}")
            
            # Display chunk type distribution
            if chunk_type_counts:
                print(f"{self.info_color}[Base Memory] Chunk type distribution:{self.reset_color}")
                for chunk_type, count in sorted(chunk_type_counts.items()):
                    print(f"  - {chunk_type}: {count}")
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to load base memory: {e}{self.reset_color}")

    def _validate_enhanced_embedding_item(self, item: Dict[str, Any]) -> bool:
        """Enhanced validation for structured embedding items"""
        required_fields = ['text', 'embedding']
        return (
            isinstance(item, dict) and
            all(field in item for field in required_fields) and
            isinstance(item['text'], str) and
            len(item['text'].strip()) > 0 and
            isinstance(item['embedding'], list) and
            len(item['embedding']) > 0
        )

    def _should_use_long_term_memory(self, query: str) -> bool:
        """Enhanced logic to determine if query needs long-term memory search"""
        # Historical indicators
        long_term_indicators = [
            "remember", "recall", "before", "previously", "earlier", 
            "told you", "mentioned", "discussed", "talked about",
            "last time", "history", "past", "ago", "when did",
            "what did", "how did", "why did", "who was", "where was"
        ]
        
        # Minecraft-specific knowledge indicators
        minecraft_knowledge_indicators = [
            "how to", "what is", "explain", "guide", "tutorial", "help",
            "craft", "make", "build", "mine", "fight", "find", "get",
            "best way", "strategy", "tips", "advice", "should i"
        ]
        
        query_lower = query.lower()
        
        # Check for historical context needs
        historical_match = any(indicator in query_lower for indicator in long_term_indicators)
        
        # Check for knowledge-seeking patterns
        knowledge_match = any(indicator in query_lower for indicator in minecraft_knowledge_indicators)
        
        # Check if query relates to Minecraft concepts
        minecraft_match = any(
            any(keyword in query_lower for keyword in keywords)
            for keywords in self.minecraft_context_patterns.values()
        )
        
        return historical_match or (knowledge_match and minecraft_match)

    def _save_memory(self):
        """Save chat entries to JSON file - individual messages, not embedded"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{self.error_color}[Error] Failed mem save: {e}{self.reset_color}")

    def _save_embeddings(self):
        """Save embedded summaries to JSON file - summaries only"""
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

    def add_summary_embedding(self, summary_text: str, metadata: Dict[str, Any] = {}):
        """Add a summary text to embeddings (used by summarizer only)"""
        if not summary_text.strip():
            return
            
        try:
            embedding = self._get_ollama_embedding(summary_text)
            if embedding is None:
                print(f"{self.error_color}[Error] Failed to get embedding for summary: {summary_text[:50]}...{self.reset_color}")
                return
            
            # Mark this as a summary embedding
            summary_metadata = metadata.copy()
            summary_metadata['entry_type'] = 'summary'
            summary_metadata['created_by'] = 'summarizer'
                
            self.embeddings_data.append({
                'text': summary_text,
                'embedding': embedding,
                'metadata': summary_metadata,
                'timestamp': self._format_timestamp()
            })
            self._save_embeddings()
            print(f"{self.system_color}[Embeddings] Added summary embedding: {summary_text[:50]}...{self.reset_color}")
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

    def _calculate_relevance_score(self, item: Dict[str, Any], query: str, base_similarity: float) -> float:
        """Enhanced relevance scoring using metadata and context"""
        score = base_similarity
        metadata = item.get('metadata', {})
        
        # Classify query intent
        query_category, confidence = self._classify_query_intent(query)
        
        # Boost score for matching chunk types
        chunk_type = metadata.get('chunk_type', 'general_guide')
        if query_category != 'general' and confidence > 0.3:
            if chunk_type == query_category:
                score += 0.2  # Strong boost for exact category match
            elif chunk_type == 'decision_guide':
                score += 0.1  # Moderate boost for decision guides
        
        # Boost for keyword matches
        keywords = metadata.get('keywords', [])
        query_words = set(query.lower().split())
        keyword_matches = len(set(keywords) & query_words)
        if keyword_matches > 0:
            score += min(0.15, keyword_matches * 0.05)
        
        # Slight boost for higher-level sections (more authoritative)
        section_level = metadata.get('section_level', 1)
        if section_level <= 2:  # Main sections
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0

    def search_embeddings(self, query: str, k: int = 5, include_base: bool = True) -> List[Dict[str, Any]]:
        """Enhanced search with smart filtering and relevance scoring"""
        all_embeddings = self.embeddings_data.copy()  # These are summaries
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
            query_category, confidence = self._classify_query_intent(query)
            
            for item in all_embeddings:
                embedding = item.get('embedding')
                if not embedding:
                    continue
                    
                base_similarity = self._cosine_similarity(query_embedding, embedding)
                
                # Apply enhanced relevance scoring
                relevance_score = self._calculate_relevance_score(item, query, base_similarity)
                
                metadata = item.get('metadata', {})
                source_type = metadata.get('source_type', 'personal')
                chunk_type = metadata.get('chunk_type', 'general')
                
                results.append({
                    'text': item['text'],
                    'similarity': float(base_similarity),
                    'relevance_score': float(relevance_score),
                    'metadata': metadata,
                    'timestamp': item.get('timestamp', ''),
                    'source_type': source_type,
                    'chunk_type': chunk_type,
                    'context_path': metadata.get('context_path', ''),
                    'keywords': metadata.get('keywords', [])
                })
            
            # Sort by relevance score (which includes similarity + metadata boosts)
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Filter for minimum relevance threshold
            filtered_results = [r for r in results if r['relevance_score'] > 0.3]
            
            return filtered_results[:k]
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to search embeddings: {e}{self.reset_color}")
            return []

    def search_by_category(self, query: str, category: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search specifically within a chunk category"""
        category_embeddings = [
            emb for emb in self.base_embeddings
            if emb.get('metadata', {}).get('chunk_type') == category
        ]
        
        if not category_embeddings:
            return []
        
        try:
            query_embedding = self._get_ollama_embedding(query)
            if query_embedding is None:
                return []
            
            results = []
            for item in category_embeddings:
                embedding = item.get('embedding')
                if not embedding:
                    continue
                    
                similarity = self._cosine_similarity(query_embedding, embedding)
                metadata = item.get('metadata', {})
                
                results.append({
                    'text': item['text'],
                    'similarity': float(similarity),
                    'metadata': metadata,
                    'context_path': metadata.get('context_path', ''),
                    'chunk_type': category
                })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:k]
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed category search: {e}{self.reset_color}")
            return []

    def search_base_memory_only(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search only base memory embeddings with enhanced relevance"""
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
                    
                base_similarity = self._cosine_similarity(query_embedding, embedding)
                relevance_score = self._calculate_relevance_score(item, query, base_similarity)
                
                metadata = item.get('metadata', {})
                
                results.append({
                    'text': item['text'],
                    'similarity': float(base_similarity),
                    'relevance_score': float(relevance_score),
                    'metadata': metadata,
                    'timestamp': item.get('timestamp', ''),
                    'source_type': 'base_memory',
                    'chunk_type': metadata.get('chunk_type', 'general'),
                    'context_path': metadata.get('context_path', '')
                })
            
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to search base memory: {e}{self.reset_color}")
            return []

    def get_memory_context_with_search(self, query: str, include_base: bool = True) -> str:
        """Force inclusion of long-term memory search regardless of query content"""
        return self.get_memory_context(query, include_base=include_base, force_long_term=True)

    def get_short_term_context_only(self) -> str:
        """Get only recent conversation context without any long-term memory"""
        context_parts = []
        
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

    def get_recent_context(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Get recent conversation entries for context"""
        if limit == 0:
            limit = self.max_context_entries
        
        recent_entries = self.memory[-limit:] if len(self.memory) > limit else self.memory
        return recent_entries

    def get_memory_context(self, query: str, include_base: bool = True, force_long_term: bool = False) -> str:
        """Enhanced memory context with better formatting and categorization"""
        context_parts = []
        
        # Enhanced long-term memory search (searches summaries + base knowledge)
        if force_long_term or self._should_use_long_term_memory(query):
            similar_memories = self.search_embeddings(query, k=5, include_base=include_base)
            
            if similar_memories:
                context_parts.append("=== RELEVANT KNOWLEDGE ===")
                
                # Group by source type and category
                base_memories = [m for m in similar_memories if m['source_type'] == 'base_memory']
                summary_memories = [m for m in similar_memories if m['source_type'] == 'personal']
                
                if base_memories:
                    context_parts.append("Knowledge Base:")
                    for memory in base_memories[:3]:  # Limit base knowledge
                        chunk_type = memory.get('chunk_type', 'guide')
                        context_path = memory.get('context_path', '')
                        context_info = f" [{chunk_type.title()}"
                        if context_path:
                            context_info += f" - {context_path}"
                        context_info += f"] (relevance: {memory['relevance_score']:.2f})"
                        
                        context_parts.append(f"- {memory['text']}{context_info}")
                
                if summary_memories:
                    context_parts.append("Personal History Summaries:")
                    for memory in summary_memories[:2]:  # Limit personal summaries
                        context_parts.append(f"- {memory['text']} [Summary] (relevance: {memory['relevance_score']:.2f})")
                
                context_parts.append("")
                print(f"{self.info_color}[Memory] Retrieved enhanced knowledge context{self.reset_color}")
        
        # Always include recent conversations (from individual chat entries)
        recent = self.get_recent_context()
        if recent:
            context_parts.append("=== RECENT CONVERSATIONS ===")
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
        print(f"{self.system_color}[Memory] Saved interaction to memory.json (not embedded){self.reset_color}")

    def get_entries_for_summarization(self, start_index: int = 0) -> List[Dict[str, Any]]:
        """Get memory entries for summarization starting from a specific index"""
        return self.memory[start_index:]

    def mark_entries_as_summarized(self, end_index: int):
        """Remove entries that have been summarized to prevent re-processing"""
        if end_index < len(self.memory):
            # Keep recent entries, remove older ones that were summarized
            self.memory = self.memory[end_index:]
            self._save_memory()
            print(f"{self.system_color}[Memory] Archived {end_index} summarized entries{self.reset_color}")

    def print_long_term_memory(self):
        """Enhanced memory statistics with chunk type breakdown"""
        print(f"[Memory] Total chat entries: {len(self.memory)}")
        print(f"[Memory] Total summary embeddings: {len(self.embeddings_data)}")
        print(f"[Memory] Total base embeddings: {len(self.base_embeddings)}")
        
        # Base memory chunk type breakdown
        if self.base_embeddings:
            chunk_types = {}
            source_files = {}
            for emb in self.base_embeddings:
                metadata = emb.get('metadata', {})
                chunk_type = metadata.get('chunk_type', 'unknown')
                source_file = metadata.get('source_file', 'unknown')
                
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                source_files[source_file] = source_files.get(source_file, 0) + 1
            
            print(f"\n=== BASE KNOWLEDGE BREAKDOWN ===")
            print("Chunk Types:")
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"  - {chunk_type}: {count}")
            
            print("Source Files:")
            for source_file, count in sorted(source_files.items()):
                print(f"  - {source_file}: {count}")
        
        if self.memory:
            print(f"\n=== RECENT CHAT ENTRIES ===")
            recent = self.memory[-10:] if len(self.memory) > 10 else self.memory
            for entry in recent:
                role = entry.get('role', '')
                content = entry.get('content', '')[:100] + "..." if len(entry.get('content', '')) > 100 else entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                print(f"[{timestamp}] {role}: {content}")

    def reload_base_memory(self):
        """Reload base memory embeddings from files"""
        print(f"{self.info_color}[Base Memory] Reloading base memory files...{self.reset_color}")
        self._load_base_memory()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Enhanced memory statistics"""
        chunk_types = {}
        for emb in self.base_embeddings:
            chunk_type = emb.get('metadata', {}).get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            'memory_entries': len(self.memory),
            'summary_embeddings_count': len(self.embeddings_data),
            'base_embeddings_count': len(self.base_embeddings),
            'chunk_types': chunk_types
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
                'summary_embeddings': self.embeddings_data,
                'base_embeddings_count': len(self.base_embeddings),
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
            
            if 'summary_embeddings' in import_data:
                self.embeddings_data.extend(import_data['summary_embeddings'])
            elif 'embeddings' in import_data:  # Legacy format
                self.embeddings_data.extend(import_data['embeddings'])
            
            self._save_memory()
            self._save_embeddings()
            
            print(f"{self.success_color}[Memory] Imported from {filepath}{self.reset_color}")
        except Exception as e:
            print(f"{self.error_color}[Error] Failed to import memory: {e}{self.reset_color}")

    def search_for_minecraft_help(self, query: str) -> str:
        """Specialized method for Minecraft-specific queries with formatted output"""
        try:
            # Classify the query intent
            query_category, confidence = self._classify_query_intent(query)
            
            # Search for relevant information
            results = self.search_base_memory_only(query, k=3)
            
            if not results:
                return f"I don't have specific information about '{query}' in my knowledge base. Could you rephrase or ask about something more specific?"
            
            # Format response based on query type
            response_parts = []
            
            if query_category != 'general' and confidence > 0.3:
                response_parts.append(f"**{query_category.title()} Guide:**")
            
            for i, result in enumerate(results[:2]):  # Limit to top 2 most relevant
                context_path = result.get('context_path', '')
                chunk_type = result.get('chunk_type', 'guide')
                
                # Add section context
                if context_path:
                    response_parts.append(f"\n*From: {context_path}*")
                
                response_parts.append(f"{result['text']}")
                
                # Add separator between results
                if i < len(results) - 1:
                    response_parts.append("\n" + "-" * 40)
            
            # Add relevance note if confidence is high
            if confidence > 0.6:
                response_parts.append(f"\n*This information is specifically relevant to {query_category} tasks.*")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            print(f"{self.error_color}[Error] Failed Minecraft help search: {e}{self.reset_color}")
            return "I encountered an error while searching for that information. Please try rephrasing your question."

    def get_minecraft_context_summary(self) -> str:
        """Get a summary of available Minecraft knowledge categories"""
        if not self.base_embeddings:
            return "No Minecraft knowledge base loaded."
        
        chunk_types = {}
        section_counts = {}
        
        for emb in self.base_embeddings:
            metadata = emb.get('metadata', {})
            chunk_type = metadata.get('chunk_type', 'unknown')
            context_path = metadata.get('context_path', 'Unknown Section')
            
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            # Extract main section from context path
            main_section = context_path.split(' > ')[0] if ' > ' in context_path else context_path
            section_counts[main_section] = section_counts.get(main_section, 0) + 1
        
        summary_parts = [
            "**Available Minecraft Knowledge:**",
            "",
            "**Categories:**"
        ]
        
        # Format chunk types nicely
        for chunk_type, count in sorted(chunk_types.items()):
            if chunk_type != 'unknown':
                summary_parts.append(f"- {chunk_type.replace('_', ' ').title()}: {count} sections")
        
        summary_parts.extend([
            "",
            "**Main Topics:**"
        ])
        
        # Show main sections
        for section, count in sorted(section_counts.items())[:8]:  # Top 8 sections
            if section and section != 'Unknown Section':
                summary_parts.append(f"- {section}: {count} chunks")
        
        summary_parts.extend([
            "",
            f"Total knowledge chunks: {len(self.base_embeddings)}",
            "",
            "Ask me anything about Minecraft gameplay, crafting, combat, building, or survival!"
        ])
        
        return "\n".join(summary_parts)

    def debug_search_results(self, query: str, k: int = 5) -> None:
        """Debug method to see detailed search results"""
        print(f"{self.info_color}[Debug] Searching for: '{query}'{self.reset_color}")
        
        query_category, confidence = self._classify_query_intent(query)
        print(f"{self.info_color}[Debug] Query category: {query_category} (confidence: {confidence:.2f}){self.reset_color}")
        
        results = self.search_embeddings(query, k=k, include_base=True)
        
        print(f"{self.info_color}[Debug] Found {len(results)} results:{self.reset_color}")
        for i, result in enumerate(results):
            print(f"\n{self.info_color}[Result {i+1}]{self.reset_color}")
            print(f"  Similarity: {result['similarity']:.3f}")
            print(f"  Relevance: {result['relevance_score']:.3f}")
            print(f"  Type: {result.get('chunk_type', 'unknown')}")
            print(f"  Context: {result.get('context_path', 'N/A')}")
            print(f"  Keywords: {result.get('keywords', [])}")
            print(f"  Text: {result['text'][:150]}...")

    def test_minecraft_categories(self) -> None:
        """Test method to verify category detection works"""
        test_queries = [
            "how to fight zombies",
            "craft a pickaxe", 
            "mine diamonds",
            "grow wheat",
            "build a house",
            "I'm hungry and low on health",
            "where can I find villages",
            "what should I do next"
        ]
        
        print(f"{self.info_color}[Test] Category detection results:{self.reset_color}")
        for query in test_queries:
            category, confidence = self._classify_query_intent(query)
            print(f"  '{query}' -> {category} ({confidence:.2f})")

# Additional utility functions for Minecraft-specific operations
def create_minecraft_query_templates() -> Dict[str, List[str]]:
    """Return common Minecraft query templates for testing"""
    return {
        'crafting': [
            "how to craft {}",
            "recipe for {}",
            "how do I make {}",
            "what materials do I need for {}"
        ],
        'combat': [
            "how to fight {}",
            "how to defeat {}",
            "best weapon against {}",
            "combat strategy for {}"
        ],
        'mining': [
            "where to find {}",
            "how to mine {}",
            "best level for {}",
            "what tool for {}"
        ],
        'building': [
            "how to build {}",
            "materials for {}",
            "design for {}",
            "construction of {}"
        ],
        'survival': [
            "how to get {}",
            "where to find {}",
            "how to avoid {}",
            "what to do when {}"
        ]
    }