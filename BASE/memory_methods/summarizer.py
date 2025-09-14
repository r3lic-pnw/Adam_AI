# Filename: BASE/memory_methods/summarizer.py
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

def summarize_memory(memory_manager, entries_to_process: Optional[int] = None) -> bool:
    """
    Summarize past days' memory entries and create embeddings for long-term storage.
    Only summaries are embedded, not individual chat entries.
    Only summarizes entries from past days, never the current day.
    
    Args:
        memory_manager: MemoryManager instance
        entries_to_process: Number of entries to process (None = all past day entries)
    
    Returns:
        bool: True if summarization was successful
    """
    try:
        # Get entries from past days only (not current day)
        past_day_entries = memory_manager.get_past_day_entries_for_summarization()
        
        if not past_day_entries:
            print(f"{memory_manager.info_color}[Summarizer] No past day entries to summarize{memory_manager.reset_color}")
            return False
        
        if len(past_day_entries) < 2:  # Need at least 2 entries to summarize
            print(f"{memory_manager.info_color}[Summarizer] Not enough past day entries to summarize ({len(past_day_entries)}){memory_manager.reset_color}")
            return False
        
        # Group entries by day
        daily_conversations = _group_entries_by_day(past_day_entries)
        
        if not daily_conversations:
            print(f"{memory_manager.info_color}[Summarizer] No valid daily conversations found{memory_manager.reset_color}")
            return False
        
        print(f"{memory_manager.system_color}[Summarizer] Processing {len(daily_conversations)} days of conversations...{memory_manager.reset_color}")
        
        summaries_created = 0
        entries_to_remove = 0
        
        for date_str, day_entries in daily_conversations.items():
            try:
                # Create summary for this day's conversation
                summary = _create_daily_conversation_summary(memory_manager, day_entries, date_str)
                
                if summary and summary.strip():
                    # Add summary as embedding (this is the only place chat content gets embedded)
                    timestamp = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
                    metadata = {
                        'entry_type': 'daily_conversation_summary',
                        'source_type': 'personal',
                        'conversation_date': date_str,
                        'entries_count': len(day_entries),
                        'summary_date': timestamp,
                        'created_by': 'summarizer'
                    }
                    
                    memory_manager.add_summary_embedding(summary, metadata)
                    summaries_created += 1
                    entries_to_remove += len(day_entries)
                    
                    print(f"{memory_manager.success_color}[Summarizer] Created daily summary for {date_str}: {summary[:80]}...{memory_manager.reset_color}")
                
            except Exception as e:
                print(f"{memory_manager.error_color}[Summarizer] Error processing day {date_str}: {e}{memory_manager.reset_color}")
                continue
        
        if summaries_created > 0:
            # Remove entries that were successfully summarized (past days only)
            memory_manager.remove_summarized_past_day_entries(entries_to_remove)
            
            print(f"{memory_manager.success_color}[Summarizer] Successfully created {summaries_created} daily summaries and removed {entries_to_remove} past day entries{memory_manager.reset_color}")
            return True
        else:
            print(f"{memory_manager.error_color}[Summarizer] No summaries were created{memory_manager.reset_color}")
            return False
            
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Summarization failed: {e}{memory_manager.reset_color}")
        return False

def _group_entries_by_day(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group memory entries by day (YYYY-MM-DD format).
    Only processes entries from past days.
    """
    if not entries:
        return {}
    
    daily_conversations = {}
    today = datetime.now(timezone.utc).date()
    
    for entry in entries:
        try:
            # Parse timestamp to get date
            timestamp_str = entry.get('timestamp', '')
            entry_datetime = _parse_human_datetime(timestamp_str)
            entry_date = entry_datetime.date()
            
            # Skip current day entries
            if entry_date >= today:
                continue
                
            date_str = entry_date.strftime('%Y-%m-%d')
            
            if date_str not in daily_conversations:
                daily_conversations[date_str] = []
            
            daily_conversations[date_str].append(entry)
            
        except Exception as e:
            print(f"Error processing entry timestamp: {e}")
            continue
    
    # Only return days with sufficient entries (at least 4 for meaningful summary)
    return {date: entries for date, entries in daily_conversations.items() if len(entries) >= 4}

def _parse_human_datetime(timestamp_str: str) -> datetime:
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

def _create_daily_conversation_summary(memory_manager, day_entries: List[Dict[str, Any]], date_str: str) -> Optional[str]:
    """
    Create a summary of a full day's conversation using the LLM.
    """
    try:
        # Format the conversation for summarization
        conversation_text = _format_conversation_for_summary(memory_manager, day_entries)
        
        if not conversation_text.strip():
            return None
        
        # Create summarization prompt for daily conversation
        summary_prompt = f"""Create a comprehensive summary of this full day's conversation between {memory_manager.username} and {memory_manager.botname} from {date_str}. 
        Summarize in the first person from the perspective of {memory_manager.botname}, the AI assistant, creating a diary entry. Focus on:
1. Key topics and themes discussed throughout the day
2. Important information shared or learned
3. Significant questions asked and answers provided
4. Any decisions, conclusions, or insights reached
5. Emotional context and relationship dynamics
6. Ongoing projects, plans, or commitments mentioned
7. Context that would be valuable for future conversations

Create a detailed but well-organized summary that captures the essence of the day's interactions. This summary will be used for long-term memory retrieval.

Conversation from {date_str}:
{conversation_text}

Daily Summary:"""

        # Call Ollama to generate summary
        summary = _call_ollama_for_summary(memory_manager, summary_prompt)
        
        return summary
        
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Error creating daily summary for {date_str}: {e}{memory_manager.reset_color}")
        return None

def _format_conversation_for_summary(memory_manager, conversation_entries: List[Dict[str, Any]]) -> str:
    """Format conversation entries into readable text for summarization."""
    formatted_lines = []
    
    for entry in conversation_entries:
        role = entry.get('role', '')
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        
        # Extract time from timestamp for daily summary
        try:
            dt = _parse_human_datetime(timestamp)
            time_str = dt.strftime("%I:%M %p")
        except:
            time_str = "Unknown time"
        
        if role == 'user':
            formatted_lines.append(f"[{time_str}] {memory_manager.username}: {content}")
        elif role == 'assistant':
            formatted_lines.append(f"[{time_str}] {memory_manager.botname}: {content}")
    
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
            "max_tokens": 500,   # More tokens for daily summaries
            "top_p": 0.9,
            "stop": ["\n\n\n", "User:", "Human:", "Assistant:", "Daily Summary for"]
        }
        
        response = requests.post(url, json=payload, timeout=120)  # Longer timeout for daily summaries
        response.raise_for_status()
        
        result = response.json()
        summary = result.get("response", "").strip()
        
        # Clean up the summary
        if summary.lower().startswith("daily summary:"):
            summary = summary[14:].strip()
        elif summary.lower().startswith("summary:"):
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
        
        # Group by day for manual summarization too
        daily_conversations = _group_entries_by_day(entries)
        
        if not daily_conversations:
            # If no daily grouping possible, treat as one summary
            summary = _create_conversation_summary_fallback(memory_manager, entries)
            date_str = "manual_range"
        else:
            # Summarize the first/largest day found
            date_str = max(daily_conversations.keys(), key=lambda x: len(daily_conversations[x]))
            summary = _create_daily_conversation_summary(memory_manager, daily_conversations[date_str], date_str)
        
        if summary and summary.strip():
            timestamp = datetime.now(timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
            metadata = {
                'entry_type': 'manual_summary',
                'source_type': 'personal',
                'range_start': start_index,
                'range_end': end_index,
                'conversation_date': date_str,
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

def _create_conversation_summary_fallback(memory_manager, entries: List[Dict[str, Any]]) -> Optional[str]:
    """Fallback summary creation for manual ranges that don't fit daily grouping."""
    try:
        conversation_text = _format_conversation_for_summary(memory_manager, entries)
        
        if not conversation_text.strip():
            return None
        
        summary_prompt = f"""Please create a concise but comprehensive summary of this conversation between {memory_manager.username} and {memory_manager.botname}. Focus on:

1. Main topics discussed
2. Important information shared
3. Questions asked and answers given
4. Any decisions or conclusions reached
5. Context that might be relevant for future conversations

Keep the summary informative but well-organized.

Conversation to summarize:
{conversation_text}

Summary:"""

        return _call_ollama_for_summary(memory_manager, summary_prompt)
        
    except Exception as e:
        print(f"{memory_manager.error_color}[Summarizer] Error creating fallback summary: {e}{memory_manager.reset_color}")
        return None

def get_summary_stats(memory_manager) -> Dict[str, Any]:
    """Get statistics about existing summaries."""
    daily_summary_count = 0
    manual_count = 0
    
    for embedding in memory_manager.embeddings_data:
        metadata = embedding.get('metadata', {})
        entry_type = metadata.get('entry_type', '')
        if entry_type == 'daily_conversation_summary':
            daily_summary_count += 1
        elif entry_type == 'manual_summary':
            manual_count += 1
    
    return {
        'total_summaries': len(memory_manager.embeddings_data),
        'daily_conversation_summaries': daily_summary_count,
        'manual_summaries': manual_count,
        'current_day_entries_remaining': len(memory_manager.memory)
    }

def get_days_available_for_summarization(memory_manager) -> List[str]:
    """Get list of past days that have entries available for summarization."""
    past_day_entries = memory_manager.get_past_day_entries_for_summarization()
    daily_conversations = _group_entries_by_day(past_day_entries)
    return list(daily_conversations.keys())