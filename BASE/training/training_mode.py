# Filename: training_mode.py
import os
import sys
import json
import time
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from BASE.tools.query import web_search_summary
from BASE.memory_methods.summarizer import summarize_memory
from BASE.memory_methods.memory_manipulation import MemoryManager
from BASE.tools.animate import WarudoManager
from BASE.resources.help import help_msg

from personality.SYS_MSG import system_prompt
from personality.bot_info import botname, username, textmodel, embedmodel, botColor, userColor, systemColor, \
    botTColor, userTColor, systemTColor, toolTColor, errorTColor, resetTColor

from core.ai_core import AICore
from core.config import Config
from core.memory_commands import MemoryCommandHandler

class TrainingModeInterface:
    def __init__(self):
        self.config = Config()
        self.ai_core = AICore(self.config)
        self.memory_command_handler = MemoryCommandHandler(self.ai_core.memory_manager, self.config)
        
        # Training-specific settings
        self.ai_core.set_training_mode(True)  # Prevent automatic memory saving
        
        # Create dedicated asyncio loop
        self.async_loop = asyncio.new_event_loop()
        threading.Thread(target=self.async_loop.run_forever, daemon=True).start()
        
        # Initialize Warudo if enabled (for testing animations during training)
        self.warudo_manager = None
        if self.config.warudo_enabled:
            self.warudo_manager = WarudoManager(
                self.config.warudo_websocket_url,
                auto_connect=self.config.warudo_auto_connect,
                timeout=self.config.warudo_connection_timeout
            )
            self.ai_core.set_warudo_manager(self.warudo_manager)
        
        # Training state
        self.last_interaction = time.time()
        self.training_session_count = 0
        
        print(systemTColor + "[Training Mode] Initialized successfully" + resetTColor)

    def print_startup_info(self):
        """Print training mode startup information"""
        print(systemTColor + "[TRAINING MODE] Ready for training interactions" + resetTColor)
        print(systemTColor + "[INFO] Responses will NOT be saved automatically" + resetTColor)
        print(systemTColor + "[INFO] Use /approve <user_input>|||<bot_response> to save interactions" + resetTColor)
        print(systemTColor + "[INFO] Available commands: /help for full list" + resetTColor)
        
        if self.warudo_manager:
            status = "connected" if self.warudo_manager.controller.ws_connected else "ready (use /warudo_connect if needed)"
            print(systemTColor + f"[Warudo] Animation system {status}" + resetTColor)
        
        # Show memory stats
        stats = self.ai_core.memory_manager.get_memory_stats()
        print(systemTColor + f"[Memory] {stats['memory_entries']} personal memories, {stats['embeddings_count']} embeddings loaded" + resetTColor)

    def handle_training_commands(self, user_text: str) -> bool:
        """Handle training-specific commands. Returns True if handled."""
        command = user_text.strip()
        
        if command.startswith("/approve "):
            # Format: /approve user_input|||bot_response
            content = command[9:].strip()
            if "|||" in content:
                user_input, bot_response = content.split("|||", 1)
                user_input = user_input.strip()
                bot_response = bot_response.strip()
                
                if user_input and bot_response:
                    # Save the approved interaction
                    self.ai_core.memory_manager.save_interaction(user_input, bot_response)
                    self.ai_core.interaction_count += 1
                    print(systemTColor + f"[Training] Approved and saved interaction #{self.ai_core.interaction_count}" + resetTColor)
                    print(systemTColor + f"  User: {user_input[:100]}..." + resetTColor)
                    print(systemTColor + f"  Bot: {bot_response[:100]}..." + resetTColor)
                    return True
                else:
                    print(errorTColor + "[Training] Invalid format: both user input and bot response required" + resetTColor)
                    return True
            else:
                print(errorTColor + "[Training] Invalid format. Use: /approve user_input|||bot_response" + resetTColor)
                return True
        
        elif command == "/training_stats":
            print(systemTColor + "[Training Session Statistics]:" + resetTColor)
            print(f"  Session interactions: {self.training_session_count}")
            print(f"  Total approved interactions: {self.ai_core.interaction_count}")
            stats = self.ai_core.memory_manager.get_memory_stats()
            print(f"  Personal Memory Entries: {stats['memory_entries']}")
            print(f"  Personal Embeddings: {stats['embeddings_count']}")
            return True
        
        elif command == "/reset_session":
            self.training_session_count = 0
            print(systemTColor + "[Training] Session counter reset" + resetTColor)
            return True
        
        elif command.startswith("/batch_approve"):
            print(systemTColor + "[Training] Batch approval mode not implemented yet" + resetTColor)
            print(systemTColor + "[Training] Use individual /approve commands for now" + resetTColor)
            return True
        
        elif command == "/training_help":
            self.print_training_help()
            return True
        
        return False

    def print_training_help(self):
        """Print training-specific help"""
        print(systemTColor + "[Training Mode Commands]:" + resetTColor)
        print("  /approve <user>|||<bot> - Approve and save an interaction to memory")
        print("  /training_stats         - Show training session statistics")
        print("  /reset_session          - Reset session interaction counter")
        print("  /training_help          - Show this training help")
        print(systemTColor + "\n[Standard Commands Available:]" + resetTColor)
        print("  /memory, /summarize, /clear_memory, /search_memory <query>")
        print("  /warudo_* commands (if Warudo enabled)")
        print("  /help - Show full command list")

    def run(self):
        """Main training mode interaction loop"""
        self.print_startup_info()
        self.print_training_help()
        
        print(systemTColor + "\n[TRAINING MODE] Enter training interactions below. Type 'exit' to quit." + resetTColor)
        
        while True:
            try:
                # Get user input
                user_text = input(userTColor + f"{username}: " + resetTColor).strip()
                
                if not user_text:
                    continue
                
                # Handle exit command
                if user_text.lower() == "exit":
                    print(systemTColor + f"[INFO] Exiting training mode after {self.training_session_count} interactions..." + resetTColor)
                    break
                
                # Handle training-specific commands first
                if self.handle_training_commands(user_text):
                    continue
                
                # Handle memory and system commands
                if self.memory_command_handler.handle_command(user_text):
                    continue
                
                # Update interaction counters
                self.last_interaction = time.time()
                self.training_session_count += 1
                
                # Generate response using AI core (training mode - won't save automatically)
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.ai_core.generate_response(user_text, mode="text"),
                        self.async_loop
                    )
                    reply = future.result()
                    
                    if reply:
                        print(botTColor + f"{botname}: {reply}" + resetTColor)
                        print(systemTColor + f"[Training] Interaction #{self.training_session_count} generated (not saved)" + resetTColor)
                        print(systemTColor + f"[Training] To approve: /approve {user_text}|||{reply}" + resetTColor)
                    else:
                        print(errorTColor + "[ERROR] No response generated" + resetTColor)
                        
                except Exception as e:
                    print(errorTColor + f"[ERROR] Response generation failed: {e}" + resetTColor)
                    import traceback
                    traceback.print_exc()
                    
            except KeyboardInterrupt:
                print(systemTColor + f"\n[INFO] Keyboard interrupt received. Exiting after {self.training_session_count} interactions..." + resetTColor)
                break
            except EOFError:
                print(systemTColor + f"\n[INFO] End of input received. Exiting after {self.training_session_count} interactions..." + resetTColor)
                break
            except Exception as e:
                print(errorTColor + f"[ERROR] Unexpected error: {e}" + resetTColor)
                continue
        
        # Final training summary
        self.print_training_summary()
        self.cleanup()
    
    def print_training_summary(self):
        """Print training session summary"""
        print(systemTColor + "\n[Training Session Summary]:" + resetTColor)
        print(f"  Total interactions generated: {self.training_session_count}")
        print(f"  Total approved interactions: {self.ai_core.interaction_count}")
        stats = self.ai_core.memory_manager.get_memory_stats()
        print(f"  Current memory entries: {stats['memory_entries']}")
        if self.training_session_count > 0:
            approval_rate = (self.ai_core.interaction_count / self.training_session_count) * 100
            print(f"  Approval rate: {approval_rate:.1f}%")
    
    def cleanup(self):
        """Clean up resources"""
        if self.warudo_manager:
            # Warudo manager cleanup if needed
            pass
        print(systemTColor + "[Training Mode] Cleanup completed. Training session ended!" + resetTColor)

if __name__ == "__main__":
    TrainingModeInterface().run()