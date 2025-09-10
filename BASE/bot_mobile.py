#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime, timezone
import os
import requests
from typing import List, Dict, Any
import sys
from pathlib import Path
# from colorama import Fore, Style
from bs4 import BeautifulSoup
from vosk import KaldiRecognizer

project_root = Path(__file__).parent.parent  # Go up to Anna_AI directory
sys.path.insert(0, str(project_root))

from personality.SYS_MSG import system_prompt, mobile_system_prompt
from personality.bot_info import botname, username, textmodel, visionmodel, embedmodel, botColor, userColor, systemTColor, \
    botTColor, userTColor, systemTColor, toolTColor, errorTColor, resetTColor

# Resolve project root: two levels up from this file (BASE → Anna_AI)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    import ollama  # type: ignore
except ModuleNotFoundError:
    ollama = None  # Will raise if used

MEMORY_ENTRY_TYPE = Dict[str, Any]
MEMORY_TYPE = List[MEMORY_ENTRY_TYPE]

def load_memory(file_path: str) -> MEMORY_TYPE:
    """Load memory entries from JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_memory(file_path: str, memory: MEMORY_TYPE) -> None:
    """Save memory entries to JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def get_human_readable_timestamp() -> str:
    """Generate human-readable timestamp in the format: 'Saturday, May 24, 2025 at 08:21 AM UTC'"""
    now = datetime.now(timezone.utc)
    return now.strftime("%A, %B %d, %Y at %I:%M %p UTC")

def add_memory_entry(memory: MEMORY_TYPE, role: str, content: str) -> None:
    """Add a new entry to memory with timestamp."""
    entry = {
        "role": role,
        "content": content,
        "timestamp": get_human_readable_timestamp()
    }
    memory.append(entry)

def format_memory_for_context(memory: MEMORY_TYPE, max_entries: int = 20) -> str:
    """Format recent memory entries for use as context in prompts."""
    if not memory:
        return ""
    
    # Get the most recent entries
    recent_entries = memory[-max_entries:]
    
    formatted_lines = ["[Recent Conversation History]"]
    for entry in recent_entries:
        role = entry["role"]
        content = entry["content"]
        timestamp = entry["timestamp"]
        formatted_lines.append(f"{role.capitalize()} ({timestamp}): {content}")
    
    return "\n".join(formatted_lines) + "\n"

def speak(text):
    """Use Termux TTS to speak the given text."""
    os.system(f'termux-tts-speak "{text}"')

speak("Hello, Bioz.")

# ----------------------------- Pure-Python Web Search ----------------------------- #

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Scrape DuckDuckGo's HTML interface for the top results.
    Returns a list of dicts with 'title', 'href', and 'snippet'.
    """
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        )
    }
    params = {"q": query}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        hits = []
        # DuckDuckGo now uses div.result__body for each hit
        for result in soup.select("div.result__body")[:max_results]:
            a = result.select_one("a.result__a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href  = a.get("href", "")
            # snippet often sits in a div.result__snippet
            snippet_tag = result.select_one("div.result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            hits.append({"title": title, "href": href, "snippet": snippet})

        return hits

    except Exception as e:
        print(
            systemTColor +
            f"[warn] Web-scrape search failed ({type(e).__name__}: {e}), skipping." +
            resetTColor
        )
        return []

def format_search_results(results: List[Dict[str, str]]) -> str:
    """
    Turn the results into a single text block for prompting.
    """
    if not results:
        return "[No web results found]\n"
    lines = ["[Web Search Results]"]
    for i, r in enumerate(results, 1):
        title = r["title"].replace("\n", " ")
        snippet = r["snippet"].replace("\n", " ")
        href = r["href"]
        lines.append(f"{i}. {title}\n   {snippet}\n")
    return "\n".join(lines) + "\n"

# ----------------------------- Ollama helpers ----------------------------- #

def ensure_ollama() -> None:
    if ollama is None:
        raise RuntimeError(
            "The `ollama` Python package is not installed.\n"
            "Install it with:\n    pip install ollama\n"
        )

def chat_with_ollama(model: str, messages: List[Dict[str, str]]) -> str:
    """
    Send a sequence of messages to the Ollama model.
    """
    if ollama is not None:
        try:
            response = ollama.chat(model=model, messages=messages)
            return response["message"]["content"].strip()
        except Exception as e:
            print(systemTColor + f"[warn] Ollama API failed ({e}), falling back to CLI." + resetTColor)

    # Fallback – use the CLI
    prompt = "\n".join(m["content"] for m in messages if m["role"] in {"system", "user"})
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ollama CLI failed (code {result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()

# ----------------------------- Main loop ----------------------------- #

def main() -> None:
    model = "gemma3:1b-it-q4_K_M"
    memory_file = os.path.join(os.path.dirname(__file__), "memory/memory.json")
    memory = load_memory(memory_file)

    print(systemTColor + f"Starting chat with Ollama model '{model}'. Type 'exit' or 'quit' to end." + resetTColor)

    try:
        ensure_ollama()
    except RuntimeError as exc:
        print(errorTColor + str(exc) + resetTColor)
        return

    while True:
        try:
            user_input = input(userTColor + "\n\nBioz: " + resetTColor).strip()
        except (EOFError, KeyboardInterrupt):
            print(systemTColor + "\nGoodbye!" + resetTColor)
            break

        if user_input.lower() in {"exit", "quit"}:
            print(systemTColor + "Goodbye!" + resetTColor)
            break

        # Handle search functionality
        search_hits = ""
        web_block = ""
        original_input = user_input
        
        if user_input[:6].lower() == "search":
            print(systemTColor + f"[ATTEMPTING SEARCH]" + resetTColor)
            user_input = user_input[7:]
            # 1) pure-Python DuckDuckGo scrape
            search_hits = search_web(user_input, max_results=5)
            web_block = format_search_results(search_hits)
            print(f"\n\n[SEARCH RESULTS]\n{web_block}\n\n")

        # Add user input to memory (store original input including "search" prefix if present)
        add_memory_entry(memory, "user", original_input)

        # Build the message sequence for the model
        memory_context = format_memory_for_context(memory, max_entries=20)
        
        if search_hits:
            messages = [
                {"role": "system", "content": mobile_system_prompt},
                {"role": "system", "content": memory_context},
                {"role": "system", "content": web_block},
                {"role": "user", "content": user_input},
            ]
        else:
            messages = [
                {"role": "system", "content": mobile_system_prompt},
                {"role": "system", "content": memory_context},
                {"role": "user", "content": user_input},
            ]

        # Query Ollama model
        try:
            response = chat_with_ollama(model, messages)
        except Exception as e:
            print(errorTColor + f"[error] {e}" + resetTColor)
            continue

        # Display response and speak it
        print(botTColor + f"\n\nEsther: {response}" + resetTColor)
        speak(response)
        
        # Add assistant response to memory
        add_memory_entry(memory, "assistant", response)
        
        # Save updated memory
        save_memory(memory_file, memory)

if __name__ == "__main__":
    main()