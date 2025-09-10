# Filename: bot.py
import os
import sys
import threading
import queue
import time
import asyncio
import requests
from datetime import datetime, timezone
from pathlib import Path
import sounddevice as sd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("OLLAMA_NUM_PARALLEL:", os.getenv('OLLAMA_NUM_PARALLEL'))

from BASE.core.ai_core import AICore
from BASE.core.config import Config
from BASE.core.memory_commands import MemoryCommandHandler
from BASE.core.control_methods import ControlManager
from BASE.tools.text_to_voice import speak_through_vbcable
from BASE.tools.voice_to_text import load_vosk_model, init_audio, start_vosk_stream, audio_callback, listen_and_transcribe
from BASE.tools.animate import WarudoManager
from personality.bot_info import botname, username, systemTColor, botTColor, userTColor, errorTColor, resetTColor, toolTColor
from personality import controls

class VTuberAI:
    def __init__(self):
        self.config = Config()
        self.ai_core = AICore(self.config, controls)
        self.control_manager = self.ai_core.get_control_manager()
        self.memory_command_handler = MemoryCommandHandler(self.ai_core.memory_manager, self.config)
        self.raw_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.audio_started = False
        self.processing = False
        self.last_interaction = time.time()
        self.speaking_thread = None
        self.keyboard_thread = None
        self.shutdown_flag = threading.Event()
        
        self.warudo_manager = None
        if self.config.warudo_enabled:
            self.warudo_manager = WarudoManager(
                self.config.warudo_websocket_url,
                auto_connect=self.config.warudo_auto_connect,
                timeout=self.config.warudo_connection_timeout
            )
            self.ai_core.set_warudo_manager(self.warudo_manager)
        
        self.async_loop = asyncio.new_event_loop()
        threading.Thread(target=self.async_loop.run_forever, daemon=True).start()
        
        print(systemTColor + "[VTuber AI] Initialized successfully" + resetTColor)
        self._print_current_settings()

    def _print_current_settings(self):
        print(systemTColor + "[Settings] Current configuration:" + resetTColor)
        print(toolTColor + f"  Vision: {controls.USE_VISION}, Search: {controls.USE_SEARCH}, Memory Search: {controls.USE_MEMORY_SEARCH}" + resetTColor)
        print(toolTColor + f"  Minecraft: {controls.PLAYING_MINECRAFT}, Group Chat: {controls.IN_GROUP_CHAT}" + resetTColor)
        print(toolTColor + f"  Animations: {controls.AVATAR_ANIMATIONS}, Speech: {controls.AVATAR_SPEECH}" + resetTColor)
        print(toolTColor + f"  Save Memory: {controls.SAVE_MEMORY}" + resetTColor)

    # Voice handling methods (delegated to BASE/tools)
    def _init_audio(self):
        return init_audio(self)
    
    def _start_vosk_stream(self):
        start_vosk_stream(self)

    def _audio_callback(self, indata, frames, time_info, status):
        return audio_callback(self, indata, frames, time_info, status)
    
    def stop_stream(self):
        sd.stop()

    def _keyboard_input_thread(self):
        """Simplified keyboard input thread that works on all systems"""
        print(systemTColor + "[Keyboard] Type your messages and press Enter (or 'exit' to quit)" + resetTColor)
        
        while not self.shutdown_flag.is_set():
            try:
                # Show prompt
                sys.stdout.write(f"{userTColor}You: {resetTColor}")
                sys.stdout.flush()
                
                user_input = input().strip()
                if user_input:
                    if user_input.lower() == "exit":
                        self.shutdown_flag.set()
                        self.text_queue.put("exit")
                        break
                    
                    # Add keyboard input to the same queue as voice
                    self.text_queue.put(user_input)
                    
            except (EOFError, KeyboardInterrupt):
                self.shutdown_flag.set()
                self.text_queue.put("exit")
                break
            except Exception as e:
                print(errorTColor + f"[Keyboard] Input error: {e}" + resetTColor)
                time.sleep(0.1)
        
        print(systemTColor + "[Keyboard] Keyboard input thread stopped" + resetTColor)

    def _handle_warudo_commands(self, user_text: str) -> bool:
        """Handle Warudo-specific commands"""
        command = user_text.lower().strip()
        if command.startswith("/warudo"):
            if self.warudo_manager:
                handled = self.warudo_manager.handle_command(command)
                if not handled:
                    print(errorTColor + "[Warudo] Unknown command." + resetTColor)
            else:
                print(errorTColor + "[Warudo] Warudo not initialized or disabled." + resetTColor)
            return True
        return False

    def _handle_control_commands(self, user_text: str) -> bool:
        """Handle control and configuration commands"""
        command = user_text.lower().strip()
        
        if command.startswith("/settings") or command == "/status":
            status_summary = self.control_manager.get_status_summary()
            print(systemTColor + status_summary + resetTColor)
            return True
        
        if command == "/help":
            self._print_help()
            return True
            
        if command.startswith("/preset "):
            preset_name = command[8:].strip()
            success = self.control_manager.load_preset(preset_name)
            if success:
                print(systemTColor + f"[Settings] Loaded preset: {preset_name}" + resetTColor)
                self._print_current_settings()
            else:
                available = ", ".join(self.control_manager.get_available_presets())
                print(errorTColor + f"[Settings] Unknown preset: {preset_name}. Available: {available}" + resetTColor)
            return True
        
        if command == "/presets":
            available = ", ".join(self.control_manager.get_available_presets())
            print(systemTColor + f"[Settings] Available presets: {available}" + resetTColor)
            return True
            
        if command == "/reset":
            self.control_manager.reset_to_defaults()
            print(systemTColor + "[Settings] Reset to defaults" + resetTColor)
            self._print_current_settings()
            return True
            
        if command == "/validate":
            is_valid = self.control_manager.validate_all_configs()
            if is_valid:
                print(systemTColor + "[Settings] Configuration is valid" + resetTColor)
            else:
                print(errorTColor + "[Settings] Configuration has issues" + resetTColor)
            return True
        
        # Individual toggle commands
        toggles = {
            "/toggle_vision": ("USE_VISION", "Vision"),
            "/toggle_search": ("USE_SEARCH", "Web Search"),
            "/toggle_memory": ("USE_MEMORY_SEARCH", "Memory Search"),
            "/toggle_minecraft": ("PLAYING_MINECRAFT", "Minecraft Mode"),
            "/toggle_groupchat": ("IN_GROUP_CHAT", "Group Chat"),
            "/toggle_animations": ("AVATAR_ANIMATIONS", "Avatar Animations"),
            "/toggle_speech": ("AVATAR_SPEECH", "Avatar Speech"),
            "/toggle_save_memory": ("SAVE_MEMORY", "Memory Saving"),
            "/toggle_logs": ("LOG_TOOL_EXECUTION", "Tool Logging"),
        }
        
        for cmd, (var_name, display_name) in toggles.items():
            if command == cmd:
                new_value = self.ai_core.toggle_control_setting(var_name)
                if new_value is not None:
                    print(systemTColor + f"[Settings] {display_name}: {'ON' if new_value else 'OFF'}" + resetTColor)
                else:
                    print(errorTColor + f"[Settings] Failed to toggle {display_name}" + resetTColor)
                return True
        
        return False

    def _print_help(self):
        """Print help information"""
        help_text = f"""
{systemTColor}=== {botname} Command Help ==={resetTColor}

{toolTColor}Basic Commands:{resetTColor}
  exit                 - Exit the program
  /help                - Show this help message
  /settings, /status   - Show current configuration
  
{toolTColor}Control Commands:{resetTColor}
  /toggle_vision       - Toggle computer vision
  /toggle_search       - Toggle web search
  /toggle_memory       - Toggle memory search
  /toggle_minecraft    - Toggle Minecraft mode
  /toggle_groupchat    - Toggle group chat mode
  /toggle_animations   - Toggle avatar animations
  /toggle_speech       - Toggle text-to-speech
  /toggle_save_memory  - Toggle memory saving
  /toggle_logs         - Toggle debug logging
  
{toolTColor}Preset Commands:{resetTColor}
  /presets             - List available presets
  /preset <name>       - Load a preset configuration
  /reset               - Reset to default settings
  /validate            - Validate current configuration
  
{toolTColor}Available Presets:{resetTColor}
  minimal, standard, full_features, minecraft, group_chat, debug
  
{toolTColor}Memory Commands:{resetTColor}
  /memory_status       - Show memory statistics
  /search_memory <query> - Search memory for specific content
  
{toolTColor}Warudo Commands (if enabled):{resetTColor}
  /warudo_connect      - Connect to Warudo
  /warudo_disconnect   - Disconnect from Warudo
  /warudo_status       - Show Warudo connection status
"""
        print(help_text)

    def _interaction_loop(self):
        print(systemTColor + "[AI] Ready for both voice and text input..." + resetTColor)
        print(systemTColor + "[INFO] Available commands: /help for full list, /settings to view current config" + resetTColor)
        print(systemTColor + "[INFO] Voice: Speak naturally | Text: Type and press Enter | Exit: Type 'exit'" + resetTColor)
        
        if self.warudo_manager:
            status = "connected" if self.warudo_manager.controller.ws_connected else "ready (use /warudo_connect if needed)"
            print(systemTColor + f"[Warudo] Animation system {status}" + resetTColor)
        
        if controls.PLAYING_MINECRAFT:
            print(systemTColor + f"[Minecraft] Integration active - endpoint: http://127.0.0.1:3001/api/act" + resetTColor)
        
        if controls.IN_GROUP_CHAT:
            print(systemTColor + "[Group Chat] Group chat mode enabled - conversation history will be tracked" + resetTColor)
        
        while not self.shutdown_flag.is_set():
            try:
                if (self.speaking_thread and self.speaking_thread.is_alive()) or self.processing:
                    time.sleep(0.1)
                    continue
                
                texts = []
                while not self.text_queue.empty():
                    try:
                        text = self.text_queue.get(timeout=0.05)
                        if text and text.strip():
                            texts.append(text)
                    except queue.Empty:
                        pass
                
                user_text = " ".join(texts).strip()
                
                if not user_text:
                    if controls.PLAYING_MINECRAFT:
                        user_text = "Describe your next action."
                    else:
                        time.sleep(0.1)
                        continue
                    
                self.last_interaction = time.time()
                
                if user_text.lower() == "exit":
                    print(systemTColor + "[INFO] 'exit' command received. Exiting loop." + resetTColor)
                    self.shutdown_flag.set()
                    break
                
                # Handle various command types
                if self.memory_command_handler.handle_command(user_text):
                    continue
                
                if self._handle_warudo_commands(user_text):
                    continue
                    
                if self._handle_control_commands(user_text):
                    continue
                    
                print(userTColor + f"{username}: {user_text}" + resetTColor)
                
                self.processing = True
                
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.ai_core.generate_response(user_text), 
                        self.async_loop
                    )
                    reply = future.result()
                    
                    if reply:
                        print(botTColor + f"{botname}: {reply}" + resetTColor)
                        
                        if controls.AVATAR_SPEECH and len(reply) < 600:
                            print(systemTColor + "[SPEECH] Initiating text-to-speech..." + resetTColor)
                            self.speaking_thread = threading.Thread(
                                target=speak_through_vbcable, args=(reply,), daemon=True
                            )
                            self.speaking_thread.start()
                        elif len(reply) >= 600:
                            print(systemTColor + "[SPEECH] Reply too long for speech (over 600 chars). Text only." + resetTColor)
                    else:
                        print(errorTColor + "[ERROR] No response generated for user input." + resetTColor)

                except Exception as e:
                    print(errorTColor + f"[ERROR] Failed during response generation: {e}" + resetTColor)
                    import traceback
                    traceback.print_exc()
                finally:
                    self.processing = False

            except Exception as e:
                print(errorTColor + f"[FATAL ERROR] Unhandled exception in interaction loop: {e}" + resetTColor)
                import traceback
                traceback.print_exc()
                break

        print(systemTColor + "[INFO] Interaction loop terminated." + resetTColor)

    def run(self):
        print(systemTColor + "[INFO] Starting VTuber AI with Dynamic Control System" + resetTColor)
        print(systemTColor + "[INFO] Voice + Text Input enabled. Type 'exit' or press Ctrl+C to stop." + resetTColor)
        print(systemTColor + "[INFO] Available commands: /help, /settings, /preset <name>, /toggle_* commands" + resetTColor)
        
        if self.warudo_manager:
            print(systemTColor + "[INFO] Warudo animations available - will auto-detect keywords in responses" + resetTColor)

        try:
            if not self.audio_started:
                try:
                    self._init_audio()
                    self._start_vosk_stream()
                    self.audio_started = True
                    print(systemTColor + "[Audio] Voice input initialized successfully" + resetTColor)
                except Exception as e:
                    print(errorTColor + f"[Audio] Voice input initialization failed: {e}" + resetTColor)
                    print(systemTColor + "[Audio] Continuing with text-only mode" + resetTColor)

            self.keyboard_thread = threading.Thread(
                target=self._keyboard_input_thread, daemon=True
            )
            self.keyboard_thread.start()

            processing_thread = threading.Thread(
                target=self._interaction_loop, daemon=False
            )
            processing_thread.start()

            try:
                while processing_thread.is_alive() and not self.shutdown_flag.is_set():
                    processing_thread.join(timeout=1.0)
            except KeyboardInterrupt:
                print(systemTColor + "\n[INFO] Keyboard interrupt received (Ctrl+C). Shutting down gracefully..." + resetTColor)
                self.shutdown_flag.set()
                self.processing = False
                
                self.raw_queue.put(b"__EXIT__")
                try:
                    self.text_queue.put("exit", timeout=1.0)
                except:
                    pass
                
                processing_thread.join(timeout=3.0)
                if processing_thread.is_alive():
                    print(systemTColor + "[WARNING] Processing thread did not stop gracefully within 3 seconds." + resetTColor)

        except KeyboardInterrupt:
            print(systemTColor + "\n[INFO] Keyboard interrupt during initialization. Exiting..." + resetTColor)
        except Exception as e:
            print(errorTColor + f"[ERROR] Unexpected error during execution: {e}" + resetTColor)
            import traceback
            traceback.print_exc()
        finally:
            print(systemTColor + "[INFO] Starting cleanup..." + resetTColor)
            self.shutdown_flag.set()
            try:
                self.raw_queue.put(b"__EXIT__")
            except:
                pass
            try:
                self.text_queue.put("exit")
            except:
                pass
            
            if self.audio_started:
                self.stop_stream()
            
            print(systemTColor + "[INFO] Cleanup completed. Goodbye!" + resetTColor)

if __name__ == "__main__":
    VTuberAI().run()