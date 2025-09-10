#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime, timezone
import os
import requests
from typing import List, Dict, Any
import sys
from pathlib import Path
from bs4 import BeautifulSoup

project_root = Path(__file__).parent.parent  # Go up to Anna_AI directory
sys.path.insert(0, str(project_root))

from personality.SYS_MSG import system_prompt, mobile_system_prompt
from personality.bot_info import (
    botname, username, textmodel, visionmodel, embedmodel,
    botColor, userColor, systemTColor, botTColor, userTColor,
    toolTColor, errorTColor, resetTColor
)

# Resolve project root: two levels up from this file (BASE → Anna_AI)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    import ollama  # type: ignore
except ModuleNotFoundError:
    ollama = None  # Will raise if used

# Removed faster_whisper import since we're not using it

MEMORY_ENTRY_TYPE = Dict[str, Any]
MEMORY_TYPE = List[MEMORY_ENTRY_TYPE]

# ----------------------------- Memory Helpers ----------------------------- #

def load_memory(file_path: str) -> MEMORY_TYPE:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_memory(file_path: str, memory: MEMORY_TYPE) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def get_human_readable_timestamp() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%A, %B %d, %Y at %I:%M %p UTC")


def add_memory_entry(memory: MEMORY_TYPE, role: str, content: str) -> None:
    entry = {"role": role, "content": content, "timestamp": get_human_readable_timestamp()}
    memory.append(entry)


def format_memory_for_context(memory: MEMORY_TYPE, max_entries: int = 20) -> str:
    if not memory:
        return ""
    recent_entries = memory[-max_entries:]
    lines = ["[Recent Conversation History]"]
    for entry in recent_entries:
        lines.append(f"{entry['role'].capitalize()} ({entry['timestamp']}): {entry['content']}")
    return "\n".join(lines) + "\n"


def speak(text):
    # Use Termux TTS
    clean_text = text.replace('"', "'").replace('`', "'")
    os.system(f'termux-tts-speak "{clean_text}"')

# ----------------------------- Web Search Helpers ----------------------------- #

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"q": query}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        hits = []
        for result in soup.select("div.result__body")[:max_results]:
            a = result.select_one("a.result__a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet = (result.select_one("div.result__snippet").get_text(strip=True)
                       if result.select_one("div.result__snippet") else "")
            hits.append({"title": title, "href": href, "snippet": snippet})
        return hits
    except Exception:
        print(systemTColor + "[warn] Web-scrape search failed, skipping." + resetTColor)
        return []


def format_search_results(results: List[Dict[str, str]]) -> str:
    if not results:
        return "[No web results found]\n"
    lines = ["[Web Search Results]"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['snippet']}\n")
    return "\n".join(lines) + "\n"

# ----------------------------- Ollama Helpers ----------------------------- #

def ensure_ollama() -> None:
    if ollama is None:
        raise RuntimeError("The `ollama` Python package is not installed. Install it with: pip install ollama")


def chat_with_ollama(model: str, messages: List[Dict[str, str]]) -> str:
    if ollama:
        try:
            response = ollama.chat(model=model, messages=messages)
            return response["message"]["content"].strip()
        except Exception:
            pass  # Fallback to CLI
    prompt = "\n".join(m["content"] for m in messages if m["role"] in {"system", "user"})
    result = subprocess.run(
        ["ollama", "run", model, prompt], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ollama CLI failed: {result.stderr.strip()}")
    return result.stdout.strip()

# ----------------------------- Interaction Modes ----------------------------- #

def choose_mode():
    print(systemTColor + "\n=== AI Assistant Mode Selection ===" + resetTColor)
    print(systemTColor + "1. Text Mode - Type your messages" + resetTColor)
    print(systemTColor + "2. Voice Mode - Speak your messages" + resetTColor)
    while True:
        choice = input(userTColor + "\nChoose mode (1 or 2): " + resetTColor).strip()
        if choice == "1":
            return "text"
        if choice == "2":
            return "voice"
        print(errorTColor + "Please enter 1 or 2." + resetTColor)


def text_mode(model: str, memory: MEMORY_TYPE, memory_file: str) -> None:
    print(systemTColor + f"=== TEXT MODE ===\nChatting with Ollama '{model}'. Type 'exit' to quit." + resetTColor)
    while True:
        try:
            user_input = input(userTColor + "\nYou: " + resetTColor).strip()
        except (EOFError, KeyboardInterrupt):
            print(systemTColor + "\nGoodbye!" + resetTColor)
            break
        if user_input.lower() in {"exit", "quit"}:
            print(systemTColor + "Goodbye!" + resetTColor)
            break
        if not user_input:
            continue
        process_user_input(user_input, model, memory, memory_file)


def voice_mode(model: str, memory: MEMORY_TYPE, memory_file: str) -> None:
    print(systemTColor + f"=== VOICE MODE ===\nVoice mode active with Ollama '{model}'. Say 'exit' to quit." + resetTColor)
    # print(systemTColor + "IMPORTANT: To use voice input, you MUST have 'termux-api' installed and Termux MUST have microphone permission." + resetTColor)
    # print(systemTColor + "Install 'termux-api' in Termux: `pkg install termux-api`" + resetTColor)
    # print(systemTColor + "Grant Microphone permission: Go to Android Settings -> Apps -> Termux -> Permissions -> Enable Microphone." + resetTColor)

    try:
        while True:
            print(systemTColor + "\n--- Press Enter to start speaking (or type 'exit' to quit) ---" + resetTColor)
            manual_trigger = input().strip().lower()
            if manual_trigger in {"exit", "quit"}:
                print(systemTColor + "Goodbye!" + resetTColor)
                break

            user_input = ""
            try:
                print(systemTColor + "Listening via Android Speech-to-Text (using termux-speech-to-text)..." + resetTColor)
                # Execute termux-speech-to-text. It returns JSON on stdout.
                result = subprocess.run(
                        ["termux-speech-to-text"],
                        capture_output=True, text=True, check=True, timeout=15
                    )
                user_input = result.stdout.strip()
                
                if result.stdout.strip():
                    try:
                        print(systemTColor + "Listening via Android Speech-to-Text (using termux-speech-to-text)..." + resetTColor)
                        result = subprocess.run(
                            ["termux-speech-to-text"],
                            capture_output=True, text=True, check=True, timeout=15
                        )
                        user_input = result.stdout.strip()
                        if user_input:
                            print(userTColor + f"\nYou (voice): {user_input}" + resetTColor)
                        else:
                            print(systemTColor + "Android Speech-to-Text returned empty text. Please try speaking louder or clearer." + resetTColor)

                    except subprocess.CalledProcessError as e:
                        print(errorTColor + f"Error executing termux-speech-to-text: {e}" + resetTColor)
                        print(errorTColor + f"Stderr: {e.stderr.strip()}" + resetTColor)
                        print(errorTColor + "Possible causes: Microphone permission denied, termux-api not installed, or speech service issue." + resetTColor)
            except FileNotFoundError:
                print(errorTColor + "Error: 'termux-speech-to-text' command not found." + resetTColor)
                print(errorTColor + "Please ensure 'termux-api' is installed: `pkg install termux-api`" + resetTColor)
            except subprocess.TimeoutExpired:
                print(errorTColor + "Speech-to-text timed out after 15 seconds. No speech detected or processing took too long." + resetTColor)
            except Exception as e:
                print(errorTColor + f"An unexpected error occurred during speech-to-text: {e}" + resetTColor)

            if not user_input:
                print(systemTColor + "No recognizable speech input. Please try again." + resetTColor)
                continue

            if user_input.lower() in {"exit", "quit", "goodbye"}:
                print(systemTColor + "Exit command received. Goodbye!" + resetTColor)
                break

            process_user_input(user_input, model, memory, memory_file, speak_response=True)

    except (EOFError, KeyboardInterrupt):
        print(systemTColor + "\nGoodbye!" + resetTColor)


def process_user_input(user_input: str, model: str, memory: MEMORY_TYPE, memory_file: str, speak_response: bool = False) -> None:
    search_hits = []
    web_block = ""
    original_input = user_input
    if user_input.lower().startswith("search "):
        hits = search_web(user_input[7:], max_results=5)
        web_block = format_search_results(hits)
        print(f"\n[SEARCH RESULTS]\n{web_block}")
    add_memory_entry(memory, "user", original_input)
    memory_context = format_memory_for_context(memory)
    if web_block:
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
    try:
        response = chat_with_ollama(model, messages)
    except Exception as e:
        print(errorTColor + f"[error] {e}" + resetTColor)
        return
    print(botTColor + f"\nAssistant: {response}" + resetTColor)
    if speak_response:
        speak(response)
    add_memory_entry(memory, "assistant", response)
    save_memory(memory_file, memory)

# ----------------------------- Main Loop ----------------------------- #

def main() -> None:
    model = "gemma3:1b-it-q4_K_M"
    memory_file = os.path.join(os.path.dirname(__file__), "memory/memory.json")
    memory = load_memory(memory_file)
    speak("Hello, Bioz.")
    try:
        ensure_ollama()
    except RuntimeError as exc:
        print(errorTColor + str(exc) + resetTColor)
        return
    mode = choose_mode()
    if mode == "text":
        text_mode(model, memory, memory_file)
    else:
        voice_mode(model, memory, memory_file)

if __name__ == "__main__":
    main()