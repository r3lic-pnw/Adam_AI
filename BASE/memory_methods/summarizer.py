# Filename: BASE/memory_methods/summarizer.py
import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def summarize_memory(memory_manager, entries_to_process: Optional[int] = None) -> bool:
    """
    Summarize recent memory entries and create embeddings for long-term storage.
    Only summaries are embedded, not individual chat entries.
    
    Args:
        memory_manager: MemoryManager instance
        entries_to_process: Number of entries to process (None = all unsummarized)
    
    Returns:
        bool: True if summarization was successful
    """
    try:
        # Get entries for summarization
        if entries_to_process:
            entries = memory_manager.get_entries_for_summarization()[-entries_to_process:]
            start_idx = len(memory_manager.memory) - entries_to_process
        else:
            entries = memory_manager.get_entries_for_summarization()
            start_idx = 0
        
        if len(entries) < 2:  # Need at least 2 entries to summarize
            print(f"{memory_manager.info_color}[Summarizer] Not enough entries to summarize ({len(entries)}){memory_manager.reset_color}")
            return False
        
        # Group entries into conversation pairs/chunks
        conversation_chunks = _group_entries_into_conversations(entries)
        
        if not conversation_chunks:
            print(f"{memory_manager.info_color}[Summarizer] No valid conversation chunks found{memory_manager.reset_color}")
            return False
        
        print(f"{memory_manager.system_color}[Summarizer] Processing {len(conversation_chunks)} conversation chunks...{memory_manager.reset_color}")
        
        summaries_created = 0
        
        for i, chunk in enumerate(conversation_chunks):
            try:
                # Create summary for this chunk
                summary = _create_conversation_summary(memory_manager, chunk, i + 1)
                
                if summary and summary.strip():
                    # Add summary as embedding (this is the only place chat content gets embedded)
                    timestamp = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
                    metadata = {
                        'entry_type': 'conversation_summary',
                        'source_type': 'personal',
                        'conversation_chunk': i + 1,
                        'entries_count': len(chunk),
                        'summary_date': timestamp,
                        'created_by': 'summarizer'
                    }
                    
                    memory_manager.add_summary_embedding(summary, metadata)
                    summaries_created += 1
                    
                    print(f"{memory_manager.success_color}[Summarizer] Created summary {i+1}: {summary[:80]}...{memory_manager.reset_color}")
                
            except Exception as e:
                print(f"{memory_manager.error_color}[Summarizer] Error processing chunk {i+1}: {e}{memory_manager.reset_color}")
                continue
        
        if summaries_created > 0:
            # Mark entries as summarized (archive them)
            if not entries_to_process:  # Only archive if we processed all entries
                memory_manager.mark_entries_as_summarized(len(entries) - 10)  # Keep last 10 entries
            
            print(f"{memory_manager.success_color}[Summarizer] Successfully created {summaries_created} summaries{memory_manager.reset_color}")
            return True
        else:
            print(f"{memory_manager.error_color}[Summarizer] No summaries were created{memory_manager.reset_color}")
            return False
            
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Summarization failed: {e}{memory_manager.reset_color}")
        return False

def _group_entries_into_conversations(entries: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Group memory entries into logical conversation chunks.
    Each chunk should be a meaningful conversation segment.
    """
    if not entries:
        return []
    
    chunks = []
    current_chunk = []
    
    for entry in entries:
        current_chunk.append(entry)
        
        # Create a new chunk every 10-15 entries or at natural breakpoints
        if len(current_chunk) >= 12:
            chunks.append(current_chunk)
            current_chunk = []
    
    # Add remaining entries as final chunk if substantial
    if len(current_chunk) >= 4:
        chunks.append(current_chunk)
    elif current_chunk and chunks:
        # Add small remainder to last chunk
        chunks[-1].extend(current_chunk)
    elif current_chunk:
        # First chunk, even if small
        chunks.append(current_chunk)
    
    return chunks

def _create_conversation_summary(memory_manager, conversation_chunk: List[Dict[str, Any]], chunk_number: int) -> Optional[str]:
    """
    Create a summary of a conversation chunk using the LLM.
    """
    try:
        # Format the conversation for summarization
        conversation_text = _format_conversation_for_summary(memory_manager, conversation_chunk)
        
        if not conversation_text.strip():
            return None
        
        # Create summarization prompt
        summary_prompt = f"""Please create a concise but comprehensive summary of this conversation between {memory_manager.username} and {memory_manager.botname}. Focus on:

1. Main topics discussed
2. Important information shared
3. Questions asked and answers given
4. Any decisions or conclusions reached
5. Context that might be relevant for future conversations

Keep the summary informative but concise (2-4 sentences typically).

Conversation to summarize:
{conversation_text}

Summary:"""

        # Call Ollama to generate summary
        summary = _call_ollama_for_summary(memory_manager, summary_prompt)
        
        return summary
        
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Error creating summary for chunk {chunk_number}: {e}{memory_manager.reset_color}")
        return None

def _format_conversation_for_summary(memory_manager, conversation_chunk: List[Dict[str, Any]]) -> str:
    """Format conversation chunk into readable text for summarization."""
    formatted_lines = []
    
    for entry in conversation_chunk:
        role = entry.get('role', '')
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        
        if role == 'user':
            formatted_lines.append(f"{memory_manager.username}: {content}")
        elif role == 'assistant':
            formatted_lines.append(f"{memory_manager.botname}: {content}")
    
    return "\n".join(formatted_lines)

def _call_ollama_for_summary(memory_manager, prompt: str) -> Optional[str]:
    """Call Ollama API to generate summary."""
    try:
        url = f"{memory_manager.ollama_endpoint}/api/generate"
        payload = {
            "model": "llama3.2:latest",  # Use a efficient model for summaries
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,  # Lower temperature for more focused summaries
            "max_tokens": 200,   # Limit summary length
            "top_p": 0.9,
            "stop": ["\n\n", "User:", "Human:", "Assistant:"]
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        summary = result.get("response", "").strip()
        
        # Clean up the summary
        if summary.lower().startswith("summary:"):
            summary = summary[8:].strip()
        
        return summary if summary else None
        
    except requests.exceptions.RequestException as e:
        print(f"{memory_manager.error_color}[Summarizer] Ollama API error: {e}{memory_manager.reset_color}")
        return None
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Error generating summary: {e}{memory_manager.reset_color}")
        return None

def manual_summarize_range(memory_manager, start_index: int, end_index: int) -> bool:
    """
    Manually summarize a specific range of memory entries.
    
    Args:
        memory_manager: MemoryManager instance
        start_index: Starting index in memory array
        end_index: Ending index in memory array
    
    Returns:
        bool: True if successful
    """
    try:
        if start_index < 0 or end_index >= len(memory_manager.memory) or start_index >= end_index:
            print(f"{memory_manager.error_color}[Summarizer] Invalid range: {start_index}-{end_index}{memory_manager.reset_color}")
            return False
        
        entries = memory_manager.memory[start_index:end_index + 1]
        conversation_chunks = [entries]  # Treat the range as one chunk
        
        summary = _create_conversation_summary(memory_manager, conversation_chunks[0], 1)
        
        if summary and summary.strip():
            timestamp = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
            metadata = {
                'entry_type': 'manual_summary',
                'source_type': 'personal',
                'range_start': start_index,
                'range_end': end_index,
                'entries_count': len(entries),
                'summary_date': timestamp,
                'created_by': 'manual_summarizer'
            }
            
            memory_manager.add_summary_embedding(summary, metadata)
            print(f"{memory_manager.success_color}[Summarizer] Manual summary created: {summary[:80]}...{memory_manager.reset_color}")
            return True
        else:
            print(f"{memory_manager.error_color}[Summarizer] Failed to create manual summary{memory_manager.reset_color}")
            return False
            
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Manual summarization failed: {e}{memory_manager.reset_color}")
        return False

def get_summary_stats(memory_manager) -> Dict[str, Any]:
    """Get statistics about existing summaries."""
    summary_count = 0
    manual_count = 0
    
    for embedding in memory_manager.embeddings_data:
        metadata = embedding.get('metadata', {})
        if metadata.get('entry_type') == 'conversation_summary':
            summary_count += 1
        elif metadata.get('entry_type') == 'manual_summary':
            manual_count += 1
    
    return {
        'total_summaries': len(memory_manager.embeddings_data),
        'conversation_summaries': summary_count,
        'manual_summaries': manual_count,
        'chat_entries_remaining': len(memory_manager.memory)
    }