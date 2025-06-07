import os
import sys
import threading
import queue
import base64
import json
import time
import asyncio
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict, Any
import pyautogui
import sounddevice as sd
from vosk import KaldiRecognizer
from colorama import Fore
# import socketio
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent.parent  # Go up to botname_AI directory
sys.path.insert(0, str(project_root))

from BASE.tools.text_to_voice import speak_through_vbcable
from BASE.tools.voice_to_text import load_vosk_model, init_audio, start_vosk_stream, audio_callback, listen_and_transcribe
from BASE.tools.query import web_search_summary
from BASE.memory_methods.summarizer import summarize_memory
from BASE.memory_methods.memory_manipulation import MemoryManager
# from BASE.mindcraft_integration.mc_methods import init_mindserver, on_mind_msg

from personality.SYS_MSG import system_prompt
from personality.bot_info import botname, username, textmodel, visionmodel, embedmodel, botColor, userColor, systemColor, \
    botTColor, userTColor, systemTColor, toolTColor, errorTColor, resetTColor

# Resolve project root: two levels up from this file (BASE → botname_AI)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Configuration ---
PROMPT_TIMEOUT = 120
VISION_KEYWORDS = ["screen", "image", "see", "look", "monitor"]
SEARCH_KEYWORDS = ["search", "find", "look up", "web", "internet"]
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "500"))
MIND_SERVER_HOST = os.getenv("MINDSERVER_HOST", "localhost")
MIND_SERVER_PORT = os.getenv("MINDSERVER_PORT", "8080")
AGENT_NAME = os.getenv("MINDCRAFT_AGENT_NAME", f"{botname}")

# Colorize Terminal Outputs
redColor = "\033[91m"
greenColor = "\033[92m"
resetColor = "\033[0m"
yellowColor = "\033[93m"
magentaColor = "\033[95m"
cyanColor = "\033[96m"
blueColor = "\033[94m"


def load_config():
    """Load configuration from JSON file with fallback to environment variables"""
    config_path = PROJECT_ROOT / "personality" / "config.json"
    
    # Default configuration
    default_config = {
        "ollama": {
            "endpoint": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "timeout": 120,
            "seed": None
        }
    }
    
    # Load from file if it exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Merge with defaults
                for section, values in file_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
    
    return default_config

# Updated Config class to use JSON config
@dataclass  
class Config:
    def __init__(self):
        json_config = load_config()
        ollama_config = json_config.get("ollama", {})
        
        # Existing fields
        self.text_llm_model: str = os.getenv("TEXT_LLM_MODEL", textmodel)
        self.vision_llm_model: str = os.getenv("VISION_LLM_MODEL", visionmodel)
        self.system_prompt: str = system_prompt
        self.embed_model: str = os.getenv("EMBED_MODEL", embedmodel)
        self.botname: str = botname
        self.ollama_endpoint: str = os.getenv("OLLAMA_ENDPOINT", ollama_config.get("endpoint", "http://localhost:11434"))
        self.vision_endpoint: str = os.getenv("VISION_MODEL_ENDPOINT", "http://localhost:11434/api/generate")
        
        # Ollama parameters with JSON config fallback
        self.ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", str(ollama_config.get("temperature", 0.7))))
        self.ollama_max_tokens: int = int(os.getenv("OLLAMA_MAX_TOKENS", str(ollama_config.get("max_tokens", 2048))))
        self.ollama_top_p: float = float(os.getenv("OLLAMA_TOP_P", str(ollama_config.get("top_p", 0.9))))
        self.ollama_top_k: int = int(os.getenv("OLLAMA_TOP_K", str(ollama_config.get("top_k", 40))))
        self.ollama_repeat_penalty: float = float(os.getenv("OLLAMA_REPEAT_PENALTY", str(ollama_config.get("repeat_penalty", 1.1))))
        self.ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", str(ollama_config.get("timeout", 120))))
        self.ollama_seed: Optional[int] = ollama_config.get("seed")
        
        # Override with environment variable if provided
        if os.getenv("OLLAMA_SEED"):
            seed_val = int(os.getenv("OLLAMA_SEED", "-1"))
            self.ollama_seed = seed_val if seed_val != -1 else None
            
        self.max_context_entries: int = 50
        self.recent_convo_limit: int = 100

config = Config()

# Create a dedicated asyncio loop in a separate thread
async_loop = asyncio.new_event_loop()
threading.Thread(target=async_loop.run_forever, daemon=True).start()

def _missing(field, idx, item):
    """Log a warning when a field is missing, and return a placeholder."""
    print(f"Search item #{idx} missing '{field}'. Keys: {list(item.keys())}")
    return f"<no {field}>"

class VTuberAI:
    def __init__(self):
        self.sio = None
        self.mindserver_connected = False

        # Queues and audio
        self.raw_queue = queue.Queue()
        self.text_queue = queue.Queue()
        
        # Initialize Memory Manager
        self.memory_manager = MemoryManager(
            project_root=PROJECT_ROOT,
            ollama_endpoint=config.ollama_endpoint,
            embed_model=config.embed_model,
            botname=config.botname,
            username=username,
            max_context_entries=config.max_context_entries
        )
        
        # Chat mode attributes
        self.chat_mode = False  # Flag to indicate if bot is in chat room mode
        self.bot_name_for_chat = None  # Name to use in chat room
        
        # Init
        # IF NOT ION GROUP CHAT, ENABLE VOICE
        # self._init_audio()
        self._init_ollama()
        
        self.msg_buffer: List[str] = []
        self.history: List[dict] = []
        self.speaking_thread: Optional[threading.Thread] = None
        self.processing = False
        self.last_interaction = time.time()
        self.botname = config.botname
        self.username = username
        self.training = False

    def _init_ollama(self):
        """Initialize Ollama client"""
        self.ollama_endpoint = config.ollama_endpoint

    def _call_ollama(self, prompt: str, model: str, system_prompt: Optional[str] = None, image_data: str = "") -> str:
        """Call Ollama API with proper vision support"""
        try:
            if image_data:
                # Use chat API for vision models with images
                url = f"{self.ollama_endpoint}/api/chat"
                
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                # Add user message with image
                user_message = {
                    "role": "user",
                    "content": prompt,
                    "images": [image_data]  # Base64 encoded image
                }
                messages.append(user_message)
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.7,
                }
            else:
                # Use generate API for text-only requests
                url = f"{self.ollama_endpoint}/api/generate"
                
                full_prompt = ""
                if system_prompt:
                    full_prompt += f"{system_prompt}\n\n"
                full_prompt += prompt
                
                payload = {
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.7,
                }
            
            print(systemTColor + f"[Ollama] Calling {model} with {'vision' if image_data else 'text'} input" + resetTColor)
            
            response = requests.post(url, json=payload, timeout=120)  # Increased timeout for vision
            response.raise_for_status()
            result = response.json()
            
            # Create a filtered copy of the result for debug output (excluding large embeddings)
            debug_result = {}
            for key, value in result.items():
                if key == "context":
                    debug_result[key] = f"<{len(value)} embeddings hidden>"
                else:
                    debug_result[key] = value
            
            print(systemTColor + "[DEBUG] Ollama Raw Response:" + resetTColor)
            print(json.dumps(debug_result, indent=2))

            # Log performance metrics
            if "created_at" in result:
                print(systemTColor + f"Created at: {result['created_at']}" + resetTColor)
            if "model" in result:
                print(systemTColor + f"Model: {result['model']}" + resetTColor)
            if "done" in result:
                print(systemTColor + f"Done: {result['done']}" + resetTColor)
            if "total_duration" in result:
                ms = result["total_duration"] / 1e6
                print(systemTColor + f"Total duration: {ms:.2f} ms" + resetTColor)

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
                print(toolTColor + "[Model Thinking Process]:" + resetTColor)
                print(toolTColor + thinking_content + resetTColor)
                print()
            
            # Clean up response
            cleaned_response = "".join(c for c in actual_response if c not in "#*`>")
            
            print(toolTColor + "[Ollama Final Response Text]:" + resetTColor, toolTColor + cleaned_response + resetTColor)
            return cleaned_response
            
        except Exception as e:
            print(errorTColor + f"[Error] Ollama API call failed: {e}" + resetTColor)
            return ""

    def summarize_memory(self):
        """Delegate to memory manager's summarize functionality"""
        return summarize_memory(self.memory_manager)

    def print_long_term_memory(self):
        """Print memory statistics and recent entries"""
        self.memory_manager.print_long_term_memory()

    def get_bot_info(self):
        """Return bot information for chat system"""
        memory_stats = self.memory_manager.get_memory_stats()
        return {
            'name': self.botname,
            'username': self.username,
            'memory_entries': memory_stats['memory_entries'],
            'embeddings_count': memory_stats['embeddings_count'],
            'last_interaction': self.last_interaction
        }

    def _init_audio(self):
        return init_audio(self)
    
    def _start_vosk_stream(self):
        start_vosk_stream(self)

    def _audio_callback(self, indata, frames, time_info, status):
        return audio_callback(self, indata, frames, time_info, status)
    
    def stop_stream(self):
        return sd.stop()

    def _capture_screenshot(self) -> str:
        print(systemTColor + "Taking screenshot" + resetTColor)
        buf = BytesIO()
        pyautogui.screenshot().save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()

    async def _generate_response_async(self, text: str, mode: str) -> str:
        """Generate response with proper vision handling and chat awareness"""
        if not text.strip():
            return ""
        
        # Check if this is a vision request
        needs_vision = any(keyword in text.lower() for keyword in VISION_KEYWORDS)
        
        # Get screenshot and vision summary if needed (only if not in chat mode for performance)
        vision_summary = ""
        screenshot_data = ""
        
        if (needs_vision or mode in ("vision", "game")) and not self.chat_mode:
            print(systemTColor + "[Vision] Taking screenshot for analysis..." + resetTColor)
            screenshot_data = self._capture_screenshot()
            
            # Get vision model summary first
            vision_prompt = f"""Describe what you see in this screenshot in detail. Focus on:
                - UI elements and text visible
                - Any applications or windows open  
                - Current state of the screen
                - Any relevant visual information

                User query: {text}"""
                
            print(toolTColor + "[Vision] Analyzing screenshot..." + resetTColor)
            vision_summary = self._call_ollama(
                vision_prompt, 
                config.vision_llm_model, 
                "You are a helpful vision assistant that describes screenshots accurately and concisely.",
                screenshot_data
            )
            
            if vision_summary:
                print(toolTColor + f"[Vision] Screenshot analyzed: {vision_summary[:100]}..." + resetTColor)
            else:
                print(errorTColor + "[Vision] Failed to analyze screenshot" + resetTColor)
        
        # Get context from memory manager
        memory_context = self.memory_manager.get_memory_context(text)
        
        # Get search results (only if not in chat mode to avoid spam)
        needs_search = any(keyword in text.lower() for keyword in SEARCH_KEYWORDS)
        search_results = web_search_summary(text) if needs_search and not self.chat_mode else "[]"

        # Build comprehensive prompt
        if self.chat_mode:
            # In chat mode, use a more conversational system prompt
            chat_system_prompt = f"""
            {config.system_prompt}
            
            IMPORTANT: You are currently in a group chat with other AI assistants and a human user. 
            - Respond naturally and conversationally
            - Keep responses concise but engaging
            - You can reference what others have said
            - Be yourself but acknowledge this is a group conversation
            - Don't repeat what others have already said
            """
            
            full_prompt = f"""
            [[SYSTEM]]
            {chat_system_prompt}
            
            [[MEMORY_CONTEXT]]
            {memory_context}
            
            [[USER_INPUT]]
            {text}
            
            Response:
            """
        else:
            # Original prompt structure for normal mode
            full_prompt = f"""
            [[SYSTEM]]
            {config.system_prompt}
            
            [[MEMORY_CONTEXT]]
            {memory_context}
            
            [[SEARCH_RESULTS]]
            {search_results}
            """
            
            # Add vision context if available
            if vision_summary:
                full_prompt += f"""
            [[VISION_ANALYSIS]]
            Current screenshot shows: {vision_summary}
            """
            
            full_prompt += f"""
            [[USER]]
            {text}
            
            Response:
            """

        print(systemTColor + f"[Prompting] Using {config.text_llm_model} for response generation" + resetTColor)
        
        # Generate final response using text model (with vision context if available)
        reply = self._call_ollama(full_prompt, config.text_llm_model)
        
        return reply.strip() if reply else ""

    async def _process_prompt_async(self, text: str, mode: str) -> str:
        """Full processing including storage - used for normal mode"""
        reply = await self._generate_response_async(text, mode)
        
        # Save to memory manager
        self.memory_manager.save_interaction(text, reply)
        return reply


    def _interaction_loop(self, get_input: Callable[[], Optional[str]], mode: str):
        print(systemTColor + f"[{mode.upper()} MODE] Listening..." + resetTColor)
        if self.training:
            print(systemTColor + "[TRAINING MODE] Responses will not be saved unless approved." + resetTColor)
        
        while True:
            if (self.speaking_thread and self.speaking_thread.is_alive()) or self.processing:
                time.sleep(0.1)
                continue
                
            texts = []
            if mode == "text":
                inp = get_input()
                if inp is None:
                    break
                texts = [inp]
            else:
                # Collect all available text from the queue
                while not self.text_queue.empty():
                    text = self.text_queue.get()
                    if text.strip():  # Only add non-empty text
                        texts.append(text)
                        
            # Join texts and check if we have actual content
            user_text = " ".join(texts).strip()
            
            # Skip processing if no text or only whitespace
            if not user_text:
                # Only check timeout if we haven't had any interaction recently
                if time.time() - self.last_interaction > PROMPT_TIMEOUT:
                    time.sleep(0.1)
                continue
                
            # Update interaction time only when we have actual text
            self.last_interaction = time.time()
            
            if user_text.lower() == "exit":
                break
            if user_text.lower() == "/memory":
                self.print_long_term_memory()
                continue
            if user_text.lower() == "/summarize":
                self.summarize_memory()
                continue
                
            print(userTColor + f"{self.username}: {user_text}" + resetTColor)
            
            # Set processing flag to prevent multiple simultaneous requests
            self.processing = True
            
            try:
                # Generate response based on mode
                if self.training:
                    # In training mode, generate response without saving
                    future = asyncio.run_coroutine_threadsafe(
                        self._generate_response_async(user_text, mode), async_loop
                    )
                    reply = future.result()
                    print(botTColor + f"{self.botname}: {reply}" + resetTColor)
                    
                    # Ask for approval before saving
                    determination = input(systemTColor + "Is this a good response? (y/n): " + resetTColor)
                    if determination.lower() == "y":
                        self.memory_manager.save_interaction(user_text, reply)
                        print(systemTColor + "[TRAINING] Response saved to memory." + resetTColor)
                    else:
                        print(errorTColor + "[TRAINING] Response discarded." + resetTColor)
                        continue
                else:
                    # In normal mode, generate and save automatically
                    future = asyncio.run_coroutine_threadsafe(
                        self._process_prompt_async(user_text, mode), async_loop
                    )
                    reply = future.result()
                    
                    # Only proceed if we got a valid reply
                    if reply and reply.strip():
                        print(botTColor + f"{self.botname}: {reply}" + resetTColor)
                        
                        # Voice synthesis for non-text modes
                        # if mode != "text" and len(reply) < 600:
                        if len(reply) < 600:
                            t = threading.Thread(
                                target=speak_through_vbcable, args=(reply,), daemon=True
                            )
                            t.start()
                            self.speaking_thread = t
                            
                        # Update history
                        self.history.extend([
                            {"role": "user", "content": user_text},
                            {"role": "assistant", "content": reply},
                        ])
                        self.msg_buffer.append(f"{self.username}: {user_text}\n{self.botname}: {reply}")
                    else:
                        print(errorTColor + "[ERROR] Received empty response from model" + resetTColor)
            
            except Exception as e:
                print(errorTColor + f"[ERROR] Failed to process response: {e}" + resetTColor)
            finally:
                # Always clear the processing flag
                self.processing = False

    def run(self):
        print("[INFO] Starting VTuber AI. Type 'exit' to quit.")
        print("[INFO] Available commands: /memory, /summarize")
        mode = (
            input(
                toolTColor
                + "Mode (text/talk/vision/game/minecraft/train): "
                + resetTColor
            )
            .strip()
            .lower()
        )
        valid = ("text", "talk", "vision", "game", "minecraft", "train")
        while mode not in valid:
            mode = (
                input("Invalid. Choose from text/talk/vision/game/minecraft/train: ")
                .strip()
                .lower()
            )
        if mode == "train":
            self.training = True
            mode = "text"
        input_getter = input if mode == "text" else lambda: None
        try:
            self._interaction_loop(input_getter, mode)
        finally:
            self.raw_queue.put(b"__EXIT__")
            self.stop_stream()
            if self.sio:
                self.sio.disconnect()


if __name__ == "__main__":
    VTuberAI().run()