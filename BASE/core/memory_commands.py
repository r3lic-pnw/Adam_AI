# Filename: core/memory_commands.py
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from BASE.resources.help import help_msg
from personality.bot_info import systemTColor, errorTColor, resetTColor

class MemoryCommandHandler:
    """Handles memory-related and system commands with proper chat/summary separation"""
    
    def __init__(self, memory_manager, config):
        self.memory_manager = memory_manager
        self.config = config

    def handle_command(self, user_text: str) -> bool:
        """Handle memory-related and system commands. Returns True if handled."""
        command = user_text.lower().strip()

        # Memory commands
        if command == "/memory":
            self.memory_manager.print_long_term_memory()
            
        elif command == "/summarize":
            try:
                from BASE.memory_methods.summarizer import summarize_memory
                summarize_memory(self.memory_manager)
            except ImportError:
                print(errorTColor + "[Error] Summarizer module not found" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Error] Summarization failed: {e}" + resetTColor)

        elif command == "/memory_mode":
            print(systemTColor + "[Memory Mode] Current behavior:" + resetTColor)
            print("- Chat entries are saved individually (not embedded)")
            print("- Only daily summaries are embedded for long-term retrieval")
            print("- Short-term memory (recent chat entries) is always used")
            print("- Long-term memory (summaries + base knowledge) is used when query suggests need for context")
            print("- Keywords that trigger long-term search: remember, recall, before, previously, etc.")
            print("- Use /search_memory <query> to manually search embedded summaries")
            print("- Use /search_base <query> to search base knowledge")
            print("- Use /force_long_term to enable long-term memory for next response")

        elif command == "/short_term_only":
            print(systemTColor + "[Memory] Showing short-term context only:" + resetTColor)
            context = self.memory_manager.get_short_term_context_only()
            if context.strip():
                print(context)
            else:
                print("No recent conversations found.")

        elif command == "/force_long_term":
            # This would need to be implemented in the AI core to force long-term memory
            print(systemTColor + "[Memory] To force long-term memory search, use keywords like:" + resetTColor)
            print("'remember', 'recall', 'what did we discuss', 'mentioned before', etc.")
            print("Or use /search_memory <query> to directly search summaries")

        elif command == "/memory_test":
            # Test what type of context would be provided
            test_query = input(systemTColor + "Enter test query: " + resetTColor)
            would_use_long_term = self.memory_manager._should_use_long_term_memory(test_query)
            print(systemTColor + f"[Memory Test] Query: '{test_query}'" + resetTColor)
            print(f"Would trigger long-term memory: {'Yes' if would_use_long_term else 'No'}")
            
            if would_use_long_term:
                context = self.memory_manager.get_memory_context(test_query)
            else:
                context = self.memory_manager.get_short_term_context_only()
            
            print("\nContext that would be provided:")
            print("-" * 50)
            print(context[:500] + "..." if len(context) > 500 else context)
            print("-" * 50)
            
        elif command == "/clear_memory":
            confirm = input(systemTColor + "Are you sure you want to clear personal memory? (y/n): " + resetTColor)
            if confirm.lower() == 'y':
                self.memory_manager.clear_memory()
                print(systemTColor + "[Memory] Personal chat entries and summaries cleared." + resetTColor)
                
        elif command == "/reload_base":
            self.memory_manager.reload_base_memory()
            
        elif command.startswith("/export_memory "):
            filepath = command.split(" ", 1)[1]
            self.memory_manager.export_memory(filepath)
            
        elif command.startswith("/import_memory "):
            filepath = command.split(" ", 1)[1]
            self.memory_manager.import_memory(filepath)
            
        elif command.startswith("/search_memory "):
            query = command.split(" ", 1)[1]
            # Search both summaries and base knowledge
            results = self.memory_manager.search_embeddings(query, k=5, include_base=True)
            print(systemTColor + f"[Memory Search] Found {len(results)} results for '{query}':" + resetTColor)
            for i, result in enumerate(results, 1):
                source_type = result.get('source_type', 'unknown')
                relevance = result.get('relevance_score', result.get('similarity', 0))
                if source_type == 'base_memory':
                    source_info = result['metadata'].get('source_file', 'unknown')
                    print(f"{i}. [Base: {source_info}] {result['text'][:100]}... (relevance: {relevance:.3f})")
                else:
                    print(f"{i}. [Summary] {result['text'][:100]}... (relevance: {relevance:.3f})")
                
        elif command.startswith("/search_summaries "):
            query = command.split(" ", 1)[1]
            # Search only personal summaries
            results = self.memory_manager.search_embeddings(query, k=5, include_base=False)
            print(systemTColor + f"[Summary Search] Found {len(results)} personal summary results for '{query}':" + resetTColor)
            for i, result in enumerate(results, 1):
                relevance = result.get('relevance_score', result.get('similarity', 0))
                timestamp = result.get('timestamp', 'Unknown time')
                print(f"{i}. [Summary - {timestamp}] {result['text'][:100]}... (relevance: {relevance:.3f})")
                
        elif command.startswith("/search_base "):
            query = command.split(" ", 1)[1]
            results = self.memory_manager.search_base_memory_only(query, k=5)
            print(systemTColor + f"[Base Memory Search] Found {len(results)} results for '{query}':" + resetTColor)
            for i, result in enumerate(results, 1):
                source_file = result['metadata'].get('source_file', 'unknown')
                context_path = result.get('context_path', '')
                relevance = result.get('relevance_score', result.get('similarity', 0))
                context_info = f" - {context_path}" if context_path else ""
                print(f"{i}. [Base: {source_file}{context_info}] {result['text'][:100]}... (relevance: {relevance:.3f})")
                
        elif command == "/memory_stats":
            stats = self.memory_manager.get_memory_stats()
            print(systemTColor + "[Memory Statistics]:" + resetTColor)
            print(f"  Chat Entries (not embedded): {stats['memory_entries']}")
            print(f"  Summary Embeddings: {stats['summary_embeddings_count']}")
            print(f"  Base Knowledge Embeddings: {stats['base_embeddings_count']}")
            print(f"  Total Searchable Embeddings: {stats['summary_embeddings_count'] + stats['base_embeddings_count']}")
            
        elif command == "/show_recent":
            limit = 10
            try:
                if " " in command:
                    limit = int(command.split(" ")[1])
            except ValueError:
                pass
            
            recent = self.memory_manager.get_recent_context(limit)
            print(systemTColor + f"[Recent {len(recent)} Chat Entries]:" + resetTColor)
            for entry in recent:
                role = entry.get('role', '').upper()
                content = entry.get('content', '')
                timestamp = entry.get('timestamp', '')
                print(f"[{timestamp}] {role}: {content}")
                
        elif command == "/debug_memory":
            print(systemTColor + "[Memory Debug Info]:" + resetTColor)
            print(f"Memory file exists: {self.memory_manager.memory_file.exists()}")
            print(f"Embeddings file exists: {self.memory_manager.embeddings_file.exists()}")
            print(f"Base memory dir exists: {self.memory_manager.base_memory_dir.exists()}")
            
            if self.memory_manager.base_memory_dir.exists():
                base_files = list(self.memory_manager.base_memory_dir.glob("*.json"))
                print(f"Base memory files found: {len(base_files)}")
                for file in base_files[:5]:  # Show first 5
                    print(f"  - {file.name}")
            
            # Show embedding model info
            print(f"Embedding model: {self.memory_manager.embed_model}")
            print(f"Ollama endpoint: {self.memory_manager.ollama_endpoint}")
            
        elif command.startswith("/test_embedding "):
            test_text = command.split(" ", 1)[1]
            print(systemTColor + f"[Testing] Creating embedding for: '{test_text}'" + resetTColor)
            embedding = self.memory_manager._get_ollama_embedding(test_text)
            if embedding:
                print(f"Success! Embedding length: {len(embedding)}")
                print(f"First 5 values: {embedding[:5]}")
            else:
                print(errorTColor + "Failed to create embedding" + resetTColor)
                
        elif command == "/minecraft_help":
            if hasattr(self.memory_manager, 'get_minecraft_context_summary'):
                summary = self.memory_manager.get_minecraft_context_summary()
                print(summary)
            else:
                print(errorTColor + "[Error] Minecraft context not available" + resetTColor)
                
        elif command.startswith("/minecraft_search "):
            query = command.split(" ", 1)[1]
            if hasattr(self.memory_manager, 'search_for_minecraft_help'):
                result = self.memory_manager.search_for_minecraft_help(query)
                print(systemTColor + "[Minecraft Help]:" + resetTColor)
                print(result)
            else:
                print(errorTColor + "[Error] Minecraft search not available" + resetTColor)
                
        # Warudo commands (delegated to warudo manager if available)
        elif command.startswith("/warudo"):
            return self._handle_warudo_command(command)
            
        # Mindcraft commands
        elif command == "/minecraft_status":
            return self._handle_minecraft_status()
            
        # Help command
        elif command == "/help":
            print(help_msg)
            # Add memory-specific help
            print("\n" + systemTColor + "=== MEMORY COMMANDS ===" + resetTColor)
            print("/memory - Show memory statistics and recent entries")
            print("/memory_stats - Show detailed memory statistics")
            print("/show_recent [N] - Show recent N chat entries")
            print("/summarize - Create summary of recent conversations")
            print("/clear_memory - Clear all personal memory")
            print("/search_memory <query> - Search summaries and base knowledge")
            print("/search_summaries <query> - Search only personal summaries")
            print("/search_base <query> - Search only base knowledge")
            print("/memory_test - Test memory context for a query")
            print("/debug_memory - Show memory system debug info")
            print("/minecraft_help - Show Minecraft knowledge summary")
            
        else:
            return False  # Command not handled

        return True  # Command was handled

    def _handle_warudo_command(self, command: str) -> bool:
        """Handle Warudo-related commands"""
        print(errorTColor + "[Warudo] Command recognized but not implemented in this handler." + resetTColor)
        print(errorTColor + "[Warudo] Use the interface-specific warudo manager directly." + resetTColor)
        return True

    def _handle_minecraft_status(self) -> bool:
        """Handle Minecraft status check"""
        try:
            import requests
            endpoint = f"http://127.0.0.1:3001/api/status"
            resp = requests.get(endpoint, timeout=5)
            if resp.ok:
                print(systemTColor + f"[Mindcraft] Status: {resp.json()}" + resetTColor)
            else:
                print(errorTColor + f"[Mindcraft] Status check failed: {resp.status_code}" + resetTColor)
        except Exception as e:
            print(errorTColor + f"[Mindcraft] Status check error: {e}" + resetTColor)
        return True