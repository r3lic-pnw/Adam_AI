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
import threading
import time
import queue
from collections import deque
import re

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

MEMORY_ENTRY_TYPE = Dict[str, Any]
MEMORY_TYPE = List[MEMORY_ENTRY_TYPE]

# Global variables for continuous listening
speech_queue = queue.Queue()
listening_active = False
processing_thread = None
listening_thread = None

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


def extract_speech_content(text: str) -> str:
    """
    Extract only the content that should be spoken, filtering out <think> tags and their contents.
    """
    # Remove <think>...</think> blocks (including multiline)
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def speak(text):
    """Use Termux TTS with Bluetooth audio routing, filtering out think tags"""
    # Extract only the speakable content
    speakable_text = extract_speech_content(text)
    
    # Only speak if there's actual content after filtering
    if not speakable_text or len(speakable_text.strip()) < 3:
        return
    
    # Clean text for TTS
    clean_text = speakable_text.replace('"', "'").replace('`', "'")
    
    # Force audio to Bluetooth if available
    os.system(f'termux-tts-speak -s BLUETOOTH_A2DP "{clean_text}" 2>/dev/null || termux-tts-speak "{clean_text}"')

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

# ----------------------------- Speech Processing ----------------------------- #

def summarize_speech_queue(speech_texts: List[str], model: str) -> str:
    """Summarize and clean up speech-to-text input using Ollama"""
    if not speech_texts:
        return ""
    
    combined_text = " ".join(speech_texts)
    return combined_text


# ----------------------------- Continuous Listening ----------------------------- #

def continuous_speech_listener():
    """Continuously listen for speech input and add to queue"""
    global listening_active, speech_queue
    
    print(systemTColor + "[info] Starting continuous speech listener..." + resetTColor)
    
    while listening_active:
        try:
            # Use termux-speech-to-text with shorter timeout for continuous listening
            result = subprocess.run(
                ["termux-speech-to-text"],  # 10 second timeout
                capture_output=True, text=True, check=True, timeout=12
            )
            
            speech_text = result.stdout.strip()
            if speech_text and len(speech_text) > 5:  # Filter out very short utterances
                timestamp = datetime.now(timezone.utc)
                speech_queue.put((timestamp, speech_text))
                print(systemTColor + f"[captured] {speech_text}" + resetTColor)
            
        except subprocess.TimeoutExpired:
            # Normal timeout, continue listening
            continue
        except subprocess.CalledProcessError as e:
            if listening_active:  # Only show error if we're still supposed to be listening
                print(systemTColor + f"[warn] Speech capture failed, retrying... ({e})" + resetTColor)
            time.sleep(1)  # Brief pause before retrying
        except FileNotFoundError:
            print(errorTColor + "[error] termux-speech-to-text not found. Install termux-api package." + resetTColor)
            break
        except Exception as e:
            if listening_active:
                print(systemTColor + f"[warn] Unexpected error in speech listener: {e}" + resetTColor)
            time.sleep(1)


def process_speech_queue(model: str, memory: MEMORY_TYPE, memory_file: str):
    """Process speech queue every X minutes"""
    global listening_active, speech_queue
    
    print(systemTColor + "[info] Starting speech queue processor (2-minute intervals)..." + resetTColor)
    
    while listening_active:
        time.sleep(120)  # Wait 2 minutes (120 seconds)
        
        if not listening_active:
            break
            
        # Collect all speech from the last 2 minutes
        speech_texts = []
        temp_queue = []
        
        # Drain the queue
        while not speech_queue.empty():
            try:
                timestamp, text = speech_queue.get_nowait()
                temp_queue.append((timestamp, text))
                speech_texts.append(text)
            except queue.Empty:
                break
        
        if not speech_texts:
            print(systemTColor + "[info] No speech captured in the last 2 minutes." + resetTColor)
            continue
            
        print(systemTColor + f"[processing] {len(speech_texts)} speech segments captured." + resetTColor)
        
        # Step 1: Summarize the speech input
        try:
            summary = summarize_speech_queue(speech_texts, model)
            if not summary or len(summary.strip()) < 5:
                print(systemTColor + "[info] Summary too short, skipping this cycle." + resetTColor)
                continue
                
            print(userTColor + f"\n[SUMMARY] {summary}" + resetTColor)
            
            # Step 2: Evaluate if search is needed
            # search_needed, search_query = evaluate_search_need(summary, model)
            search_needed, search_query = False, ""
            
            search_summary = ""
            if search_needed and search_query:
                print(systemTColor + f"[SEARCHING] Query: {search_query}" + resetTColor)
                
                # Step 3: Conduct search and summarize results
                search_results = search_web(search_query, max_results=5)
                # search_summary = summarize_search_results(search_results, search_query, model)
                
                print(toolTColor + f"[SEARCH RESULTS] {search_summary}" + resetTColor)
            else:
                print(systemTColor + "[info] No search needed for this input." + resetTColor)
            
            # Step 4: Process with assistant using both summaries
            process_summarized_input(summary, search_summary, model, memory, memory_file)
            
        except Exception as e:
            print(errorTColor + f"[error] Failed to process speech queue: {e}" + resetTColor)


def process_summarized_input(summary: str, search_summary: str, model: str, memory: MEMORY_TYPE, memory_file: str):
    """Process the summarized input with the assistant"""
    
    # Add summary to memory as user input
    add_memory_entry(memory, "user", summary)
    
    # Build context
    memory_context = format_memory_for_context(memory)
    
    # Build messages with search context if available
    if search_summary:
        messages = [
            {"role": "system", "content": mobile_system_prompt},
            {"role": "system", "content": memory_context},
            {"role": "system", "content": f"[Web Search Context]\n{search_summary}\n"},
            {"role": "user", "content": summary},
        ]
    else:
        messages = [
            {"role": "system", "content": mobile_system_prompt},
            {"role": "system", "content": memory_context},
            {"role": "user", "content": summary},
        ]
    
    try:
        response = chat_with_ollama(model, messages)
        
        # Print the full response (including think tags if present)
        print(botTColor + f"\n[ASSISTANT] {response}" + resetTColor)
        
        # Extract the speakable content (without think tags)
        speakable_response = extract_speech_content(response)
        
        # Speak only the filtered response (without think tags)
        speak(response)
        
        # Save only the filtered response to memory (without think tags)
        if speakable_response.strip():
            add_memory_entry(memory, "assistant", speakable_response)
            save_memory(memory_file, memory)
        
    except Exception as e:
        print(errorTColor + f"[error] Assistant response failed: {e}" + resetTColor)

# ----------------------------- Main Passive Listening Mode ----------------------------- #

def passive_listening_mode(model: str, memory: MEMORY_TYPE, memory_file: str):
    """Main passive listening mode with continuous speech capture"""
    global listening_active, processing_thread, listening_thread
    
    print(systemTColor + "=== PASSIVE LISTENING MODE ===" + resetTColor)
    print(systemTColor + "The bot is now listening continuously through your Bluetooth earpiece." + resetTColor)
    print(systemTColor + "Speech will be processed every few minutes with intelligent search." + resetTColor)
    print(systemTColor + "Type 'stop' and press Enter to exit." + resetTColor)
    
    # Check for Bluetooth audio devices
    try:
        result = subprocess.run(["termux-audio-info"], capture_output=True, text=True, timeout=5)
        if "BLUETOOTH" in result.stdout.upper():
            print(systemTColor + "[info] Bluetooth audio device detected." + resetTColor)
        else:
            print(systemTColor + "[warn] No Bluetooth audio detected. Audio will use default output." + resetTColor)
    except:
        pass  # Continue regardless
    
    listening_active = True
    
    # Start background threads
    listening_thread = threading.Thread(target=continuous_speech_listener, daemon=True)
    processing_thread = threading.Thread(target=process_speech_queue, args=(model, memory, memory_file), daemon=True)
    
    listening_thread.start()
    processing_thread.start()
    
    try:
        while True:
            user_command = input().strip().lower()
            if user_command in {'terminate'}:
                print(systemTColor + "Stopping passive listening mode..." + resetTColor)
                break
            elif user_command == 'status':
                queue_size = speech_queue.qsize()
                print(systemTColor + f"[status] Queue size: {queue_size} speech segments" + resetTColor)
            elif user_command == 'help':
                print(systemTColor + "Commands: 'stop' (exit), 'status' (queue info), 'help' (this message)" + resetTColor)
    except (EOFError, KeyboardInterrupt):
        print(systemTColor + "\nStopping passive listening mode..." + resetTColor)
    finally:
        listening_active = False
        # Give threads time to finish
        time.sleep(1)
        print(systemTColor + "Goodbye!" + resetTColor)

# ----------------------------- Legacy Interaction Modes ----------------------------- #

def choose_mode():
    print(systemTColor + "\n=== AI Assistant Mode Selection ===" + resetTColor)
    print(systemTColor + "1. Passive Listening Mode - Continuous earpiece listening (RECOMMENDED)" + resetTColor)
    print(systemTColor + "2. Text Mode - Type your messages" + resetTColor)
    print(systemTColor + "3. Voice Mode - Manual voice input" + resetTColor)
    while True:
        choice = input(userTColor + "\nChoose mode (1, 2, or 3): " + resetTColor).strip()
        if choice == "1":
            return "passive"
        if choice == "2":
            return "text"
        if choice == "3":
            return "voice"
        print(errorTColor + "Please enter 1, 2, or 3." + resetTColor)


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

    try:
        while True:
            print(systemTColor + "\n--- Press Enter to start speaking (or type 'exit' to quit) ---" + resetTColor)
            manual_trigger = input().strip().lower()
            if manual_trigger in {"exit", "quit"}:
                print(systemTColor + "Goodbye!" + resetTColor)
                break

            user_input = ""
            try:
                print(systemTColor + "Listening via Android Speech-to-Text..." + resetTColor)
                result = subprocess.run(
                    ["termux-speech-to-text"],
                    capture_output=True, text=True, check=True, timeout=15
                )
                user_input = result.stdout.strip()
                
                if user_input:
                    print(userTColor + f"\nYou (voice): {user_input}" + resetTColor)
                else:
                    print(systemTColor + "No speech detected. Please try again." + resetTColor)

            except subprocess.CalledProcessError as e:
                print(errorTColor + f"Error executing termux-speech-to-text: {e}" + resetTColor)
            except FileNotFoundError:
                print(errorTColor + "Error: 'termux-speech-to-text' command not found." + resetTColor)
                print(errorTColor + "Please ensure 'termux-api' is installed: `pkg install termux-api`" + resetTColor)
            except subprocess.TimeoutExpired:
                print(errorTColor + "Speech-to-text timed out after 15 seconds." + resetTColor)
            except Exception as e:
                print(errorTColor + f"An unexpected error occurred: {e}" + resetTColor)

            if not user_input:
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
    # if user_input.lower().startswith("search "):
    if user_input.lower() in {"search", "question", "unsure", "find"}:
        hits = search_web(user_input, max_results=5)
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
    
    # Print the full response (including think tags if present)
    print(botTColor + f"\nAssistant: {response}" + resetTColor)
    
    # Extract the speakable content (without think tags)
    speakable_response = extract_speech_content(response)
    
    # Speak only the filtered response (without think tags)
    if speak_response:
        speak(response)
    
    # Save only the filtered response to memory (without think tags)
    if speakable_response.strip():
        add_memory_entry(memory, "assistant", speakable_response)
        save_memory(memory_file, memory)

# ----------------------------- Main Loop ----------------------------- #

def main() -> None:
    model = textmodel  # Now uses the model from bot_info
    memory_file = os.path.join(os.path.dirname(__file__), "memory/memory.json")
    memory = load_memory(memory_file)
    
    speak("Hello, Bioz. Passive listening system ready.")
    
    try:
        ensure_ollama()
    except RuntimeError as exc:
        print(errorTColor + str(exc) + resetTColor)
        return
    
    mode = choose_mode()
    if mode == "passive":
        passive_listening_mode(model, memory, memory_file)
    elif mode == "text":
        text_mode(model, memory, memory_file)
    else:
        voice_mode(model, memory, memory_file)

if __name__ == "__main__":
    main()