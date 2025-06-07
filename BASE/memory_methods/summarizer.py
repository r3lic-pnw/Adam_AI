from datetime import datetime, timedelta, timezone
from colorama import Fore
import os
import requests
import json

from personality.bot_info import textmodel

def summarize_memory(memory_manager):
    """
    Summarize complete days of conversation history into daily summaries.
    Only complete days (midnight to 11:59:59 PM) are summarized.
    
    Args:
        memory_manager: MemoryManager instance that contains the memory and methods
    """
    now = datetime.now(timezone.utc)
    text_llm_model: str = os.getenv("TEXT_LLM_MODEL", textmodel)

    # Parse and sort entries by timestamp
    entries = []
    for e in memory_manager.memory:
        raw_ts = e.get('timestamp')
        if not raw_ts:
            continue
            
        try:
            ts = memory_manager._parse_human_datetime(raw_ts)
            entries.append((ts, e))
        except Exception as ex:
            print(f"[Warning] Could not parse timestamp '{raw_ts}': {ex}")
            continue
    
    if not entries:
        print(Fore.CYAN + "No entries to summarize." + Fore.RESET)
        return
    
    entries.sort(key=lambda x: x[0])
    print(Fore.CYAN + f"Summarizing memory from {len(entries)} entries..." + Fore.RESET)
    
    # Group entries by date
    daily_groups = {}
    for ts, entry in entries:
        date_key = ts.date()
        if date_key not in daily_groups:
            daily_groups[date_key] = []
        daily_groups[date_key].append((ts, entry))
    
    summaries = []
    summarized_dates = set()
    
    # Process complete days (exclude today since it's not complete)
    today = now.date()
    
    for date_key in sorted(daily_groups.keys()):
        if date_key >= today:
            continue  # Skip today and future dates
            
        day_entries = daily_groups[date_key]
        
        if day_entries:
            # Build conversation text for this day
            conversation_parts = []
            user_entries = [e for ts, e in day_entries if e.get('role') == 'user']
            assistant_entries = [e for ts, e in day_entries if e.get('role') == 'assistant']
            
            # Pair up user and assistant entries
            for i in range(min(len(user_entries), len(assistant_entries))):
                user_entry = user_entries[i]
                assistant_entry = assistant_entries[i]
                
                timestamp = user_entry.get('timestamp', '')
                conversation_parts.append(f"[{timestamp}]")
                conversation_parts.append(f"{memory_manager.username}: {user_entry['content']}")
                conversation_parts.append(f"{memory_manager.botname}: {assistant_entry['content']}")
                conversation_parts.append("")  # Add spacing
            
            if conversation_parts:
                conversation_text = '\n'.join(conversation_parts)
                
                # Generate summary with human-readable date
                date_str = date_key.strftime("%A, %B %d, %Y")
                
                prompt = (f"Summarize these interactions from {date_str} "
                        f"as a personal diary entry from the AI assistant {memory_manager.botname}'s perspective. Use 'I' instead of {memory_manager.botname}. Focus on key topics, emotions, and memorable moments. "
                        f"Summarize in one paragraph only. Do not create a dialog. Do not quote text from the conversation. Write the summary as a recollection "
                         "of events, interactions, and details from the assistant's perspective. Mention the names of those conversed with. The following is the conversation to summarize:\n\n"
                        f"{conversation_text}")
                print(Fore.CYAN + f"{prompt}" + Fore.RESET)
                try:
                    summary = _call_ollama_for_summary(prompt, text_llm_model, memory_manager.ollama_endpoint)

                    summary_accepted = False
                    while not summary_accepted:
                        if input(Fore.CYAN + "Is this summary acceptable? (y/n)" + Fore.RESET) != "y":
                            print(Fore.RED + "Discarded. Running new summarization..." + Fore.RESET)
                            summary = _call_ollama_for_summary(prompt, text_llm_model, memory_manager.ollama_endpoint)
                        else:
                            summary_accepted = True
            
                    if summary.strip():  # Only add non-empty summaries
                        summary_text = f"Daily Summary ({date_str}): {summary.strip()}"
                        
                        # Add to embeddings
                        memory_manager.add_embedding(summary_text, {
                            'type': 'daily_summary',
                            'date': date_str
                        })
                        
                        summaries.append({
                            'type': 'daily_summary',
                            'date': date_str,
                            'summary': summary.strip(),
                            'timestamp': datetime.combine(date_key, datetime.min.time()).replace(tzinfo=timezone.utc).strftime("%A, %B %d, %Y at %I:%M %p UTC")
                        })
                        print(Fore.YELLOW + f"Created daily summary for {date_str}" + Fore.RESET)
                        
                        # Mark this date as successfully summarized
                        summarized_dates.add(date_key)
                except Exception as e:
                    print(f"[Error] Failed to generate summary for {date_str}: {e}")
    
    # Keep only entries that were NOT successfully summarized
    # This includes today's entries and any entries from dates that failed to summarize
    new_memory = []
    for entry in memory_manager.memory:
        raw_ts = entry.get('timestamp')
        if not raw_ts:
            # Keep entries without timestamps
            new_memory.append(entry)
            continue
            
        try:
            ts = memory_manager._parse_human_datetime(raw_ts)
            entry_date = ts.date()
            if entry_date not in summarized_dates:
                new_memory.append(entry)
        except Exception:
            # Keep entries with unparseable timestamps
            new_memory.append(entry)
    
    memory_manager.memory = new_memory
    memory_manager._save_memory()
    print(Fore.GREEN + f"Memory summarization complete. "
                      f"Created {len(summaries)} daily summaries, "
                      f"kept {len(memory_manager.memory)} recent entries." + Fore.RESET)


def _call_ollama_for_summary(prompt: str, model: str, ollama_endpoint: str) -> str:
    """
    Helper function to call Ollama API for summarization
    
    Args:
        prompt: The summarization prompt
        model: The model to use
        ollama_endpoint: The Ollama endpoint URL
        
    Returns:
        The generated summary text
    """
    try:
        url = f"{ollama_endpoint}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
        }
        
        print(Fore.CYAN + f"[Summarizer] Calling {model} for summarization" + Fore.RESET)
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        # Extract content from response
        content = ""
        if "response" in result:
            content = result["response"]
        elif "message" in result and "content" in result["message"]:
            content = result["message"]["content"]
        elif "choices" in result and result["choices"]:
            content = result["choices"][0].get("message", {}).get("content", "")
        
        # Parse thinking tags and actual response
        raw_content = content.strip()
        thinking_content = ""
        actual_response = raw_content
        
        if "<think>" in raw_content and "</think>" in raw_content:
            import re
            # Use raw strings to properly handle the regex pattern
            think_pattern = r'<think>(.*?)</think>'
            think_match = re.search(think_pattern, raw_content, re.DOTALL)
            if think_match:
                thinking_content = think_match.group(1).strip()
                actual_response = re.sub(think_pattern, '', raw_content, flags=re.DOTALL).strip()
        
        if thinking_content:
            print(Fore.MAGENTA + "[Summarizer Thinking Process]:" + Fore.RESET)
            print(Fore.MAGENTA + thinking_content + Fore.RESET)
            print()
        
        # Clean up response
        cleaned_response = "".join(c for c in actual_response if c not in "#*`>").strip()
        
        print(Fore.CYAN + f"[Summarizer] Generated summary: {cleaned_response}..." + Fore.RESET)
        return cleaned_response
        
    except Exception as e:
        print(Fore.RED + f"[Error] Ollama API call failed during summarization: {e}" + Fore.RESET)
        return ""