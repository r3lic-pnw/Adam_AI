# Filename: gui_components.py
"""
Component managers for voice processing and control panel functionality.
Updated to match ai_core.py refactoring with day-based memory system and new controls.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import numpy as np
from gui_themes import DarkTheme

try:
    from BASE.tools.voice_to_text import load_vosk_model
    from personality.bot_info import botname, username
    from personality import controls
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")

class VoiceManager:
    """Manages voice input functionality"""
    
    def __init__(self, message_queue, input_queue, log_function):
        self.message_queue = message_queue
        self.input_queue = input_queue
        self.log_system_message = log_function
        
        self.voice_enabled = False
        self.audio_started = False
        self.vosk_model = None
        self.recognizer = None
        self.stream = None
        self.voice_thread = None
        
        # GUI components
        self.voice_button = None
        self.voice_status = None

    def create_voice_panel(self, parent_frame):
        """Create voice control panel"""
        voice_frame = ttk.LabelFrame(parent_frame, text="Voice Control", style="Dark.TLabelframe")
        voice_frame.pack(fill=tk.X, pady=(0, 5))
        
        voice_controls = ttk.Frame(voice_frame)
        voice_controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.voice_button = ttk.Button(
            voice_controls,
            text="Start Voice Input",
            command=self.toggle_voice_input,
            width=20
        )
        self.voice_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.voice_status = tk.Label(
            voice_controls,
            text="Voice: Disabled",
            font=("Arial", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARK
        )
        self.voice_status.pack(side=tk.LEFT)

    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        if not self.voice_enabled:
            try:
                self.log_system_message("Initializing voice input...")
                self.init_audio()
                self.voice_enabled = True
                self.voice_button.config(text="Stop Voice Input")
                self.voice_status.config(text="Voice: Listening...", foreground=DarkTheme.ACCENT_GREEN)
                self.log_system_message("Voice input started successfully")
                
                # Start voice processing thread
                self.voice_thread = threading.Thread(target=self.voice_processing_loop, daemon=True)
                self.voice_thread.start()
                
            except Exception as e:
                self.log_system_message(f"Voice processing error: {str(e)}")
                self.voice_enabled = False
                time.sleep(1)
        else:
            self.stop_voice_input()

    def init_audio(self):
        """Initialize Vosk model for voice recognition"""
        if self.vosk_model is None:
            try:
                self.log_system_message("Loading Vosk model...")
                self.vosk_model = load_vosk_model()
                self.recognizer = KaldiRecognizer(self.vosk_model, 16000)
                self.log_system_message("Vosk model loaded successfully.")
            except Exception as e:
                self.log_system_message(f"Failed to load Vosk model: {str(e)}")
                raise

    def stop_voice_input(self):
        """Stop voice input and update GUI"""
        try:
            self.voice_enabled = False
            if self.voice_button:
                self.voice_button.config(text="Start Voice Input")
            if self.voice_status:
                self.voice_status.config(text="Voice: Disabled", foreground=DarkTheme.FG_MUTED)
            self.log_system_message("Voice input stopped")
            
            # Stop audio stream if running
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception as e:
                    self.log_system_message(f"Error stopping audio stream: {str(e)}")
                self.stream = None
                
            # Wait for voice thread to finish
            if self.voice_thread and self.voice_thread.is_alive():
                self.voice_thread.join(timeout=2.0)
                
        except Exception as e:
            self.log_system_message(f"Error in stop_voice_input: {str(e)}")
    
    def voice_processing_loop(self):
        """Process voice input in a background thread"""
        try:
            if self.vosk_model is None or self.recognizer is None:
                self.log_system_message("Vosk model not loaded. Cannot start voice recognition.")
                return

            def audio_callback(indata, frames, time, status):
                """Audio callback function to process incoming audio data"""
                if status:
                    self.log_system_message(f"Audio status: {status}")
                
                # Convert audio to bytes and process with Vosk
                audio_data = (indata * 32767).astype(np.int16).tobytes()
                
                if self.recognizer is not None and hasattr(self.recognizer, "AcceptWaveform"):
                    if self.recognizer.AcceptWaveform(audio_data):
                        # Final result
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        
                        if text and len(text) >= 3:  # Minimum length check
                            # Filter out bot name mentions
                            if botname.lower() not in text.lower():
                                # Queue the recognized text
                                self.message_queue.put(("voice_input", username, text))
                                self.input_queue.put(text)
                                self.log_system_message(f"Voice recognized: {text}")

            # Start audio stream with callback
            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='float32',
                callback=audio_callback,
                blocksize=4096
            )
            
            self.stream.start()
            self.log_system_message("Voice stream started successfully.")
            
            # Keep the thread alive while voice is enabled
            while self.voice_enabled:
                time.sleep(0.1)
                
        except Exception as e:
            self.log_system_message(f"Voice processing error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up audio stream
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                    self.log_system_message("Voice stream stopped.")
                except Exception as e:
                    self.log_system_message(f"Error stopping voice stream: {str(e)}")
                self.stream = None


class ControlPanelManager:
    """Manages the control panel with all boolean variables - updated for ai_core.py refactoring"""
    
    def __init__(self, ai_core, log_function):
        self.ai_core = ai_core
        self.control_manager = ai_core.get_control_manager()
        self.log_system_message = log_function
        
        self.control_vars = {}
        self.status_labels = {}

    def create_control_panel(self, parent_frame):
        """Create comprehensive control panel with all boolean variables from controls.py"""
        
        # Create scrollable frame for controls
        control_canvas = tk.Canvas(parent_frame, bg=DarkTheme.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=control_canvas.yview)
        scrollable_frame = ttk.Frame(control_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all"))
        )
        
        control_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        control_canvas.configure(yscrollcommand=scrollbar.set)
        
        control_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        control_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Updated control groups to match ai_core.py refactoring
        control_groups = {
            "AI Capabilities": [
                ("Web Search", "USE_SEARCH", "Enable web search functionality"),
                ("Computer Vision", "USE_VISION", "Enable computer vision/screenshot analysis"),
                ("Long Memory Search", "USE_LONG_MEMORY", "Enable long-term memory search (daily summaries + base knowledge)"),
            ],
            "Game Integration": [
                ("Minecraft Mode", "PLAYING_MINECRAFT", "Enable Minecraft bot integration"),
            ],
            "Prompt Components": [
                ("System Prompt", "INCLUDE_SYSTEM_PROMPT", "Include system/personality prompt"),
                ("Vision Results", "INCLUDE_VISION_RESULTS", "Include vision analysis in prompt"),
                ("Search Results", "INCLUDE_SEARCH_RESULTS", "Include web search results in prompt"),
                ("Base Memory", "INCLUDE_BASE_MEMORY", "Include BASE memory context"),
                ("Short Memory", "INCLUDE_SHORT_MEMORY", "Include recent conversation history"),
                ("Long Memory", "INCLUDE_LONG_MEMORY", "Include summary search"),
            ],
            "Minecraft Specific": [
                ("Minecraft Context", "INCLUDE_MINECRAFT_CONTEXT", "Include Minecraft environment data"),
                ("Send MC Message", "SEND_MINECRAFT_MESSAGE", "Send responses to Minecraft chat"),
                ("Send MC Command", "SEND_MINECRAFT_COMMAND", "Execute Minecraft commands from responses"),
            ],
            "Output Actions": [
                ("Avatar Animations", "AVATAR_ANIMATIONS", "Trigger avatar animations from responses"),
                ("Avatar Speech", "AVATAR_SPEECH", "Enable text-to-speech output"),
            ],
            "Debugging & Logging": [
                ("Log Tool Execution", "LOG_TOOL_EXECUTION", "Log when tools are executed"),
                ("Log Prompt Construction", "LOG_PROMPT_CONSTRUCTION", "Log prompt building process"),
                ("Log Response Processing", "LOG_RESPONSE_PROCESSING", "Log response generation steps"),
                ("Log Minecraft Execution", "LOG_MINECRAFT_EXECUTION", "Log Minecraft-specific operations"),
            ],
            "Memory Management": [
                ("Save Memory", "SAVE_MEMORY", "Save conversations to day-based memory system"),
            ]
        }
        
        # Create control sections
        for group_name, controls_list in control_groups.items():
            self.create_control_group(scrollable_frame, group_name, controls_list)
        
        # Add global control buttons
        global_frame = ttk.LabelFrame(scrollable_frame, text="Global Controls", style="Dark.TLabelframe")
        global_frame.pack(fill=tk.X, padx=5, pady=5)
        
        button_frame = ttk.Frame(global_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Enable All", 
                   command=self.enable_all_controls, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Disable All", 
                   command=self.disable_all_controls, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Reset All", 
                   command=self.reset_controls, width=12).pack(side=tk.LEFT, padx=2)

        # Updated memory management section to match day-based system
        memory_frame = ttk.LabelFrame(scrollable_frame, text="Memory Management (Day-Based)", style="Dark.TLabelframe")
        memory_frame.pack(fill=tk.X, padx=5, pady=5)
        
        memory_button_frame = ttk.Frame(memory_frame)
        memory_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(memory_button_frame, text="Manual Summarize", 
                   command=self.manual_summarize, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(memory_button_frame, text="Force Cleanup", 
                   command=self.force_cleanup, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(memory_button_frame, text="Memory Debug", 
                   command=self.show_memory_debug, width=15).pack(side=tk.LEFT, padx=2)

        # Add Warudo connection status and control
        warudo_frame = ttk.LabelFrame(scrollable_frame, text="Warudo Integration", style="Dark.TLabelframe")
        warudo_frame.pack(fill=tk.X, padx=5, pady=5)
        
        warudo_controls = ttk.Frame(warudo_frame)
        warudo_controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.warudo_status_label = tk.Label(
            warudo_controls,
            text="Status: Unknown",
            font=("Arial", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARK
        )
        self.warudo_status_label.pack(side=tk.LEFT)
        
        ttk.Button(warudo_controls, text="Check Status", 
                   command=self.check_warudo_status, width=12).pack(side=tk.RIGHT, padx=2)

    def create_control_group(self, parent, group_name, controls_list):
        """Create a control group with checkboxes"""
        group_frame = ttk.LabelFrame(parent, text=group_name, style="Dark.TLabelframe")
        group_frame.pack(fill=tk.X, padx=5, pady=2)
        
        for display_name, var_name, description in controls_list:
            control_frame = ttk.Frame(group_frame)
            control_frame.pack(fill=tk.X, padx=5, pady=1)
            
            # Get current value
            current_value = getattr(controls, var_name, False)
            bool_var = tk.BooleanVar(value=current_value)
            self.control_vars[var_name] = bool_var
            
            # Create checkbox
            checkbox = ttk.Checkbutton(
                control_frame,
                text=display_name,
                variable=bool_var,
                command=lambda vn=var_name: self.toggle_control(vn)
            )
            checkbox.pack(side=tk.LEFT)
            
            # Add status indicator
            status_color = DarkTheme.ACCENT_GREEN if current_value else DarkTheme.FG_MUTED
            status_label = tk.Label(
                control_frame, 
                text=f"({'ON' if current_value else 'OFF'})", 
                font=("Arial", 8), 
                foreground=status_color,
                background=DarkTheme.BG_DARK,
                width=5
            )
            status_label.pack(side=tk.RIGHT)
            self.status_labels[var_name] = status_label
            
            # Add tooltip if description exists
            if description:
                self.create_tooltip(checkbox, description)

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip.configure(bg=DarkTheme.BG_DARKER)
            
            label = tk.Label(
                tooltip, 
                text=text, 
                background=DarkTheme.BG_DARKER, 
                foreground=DarkTheme.FG_PRIMARY,
                font=("Arial", 9),
                wraplength=300
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def enable_all_controls(self):
        """Enable all boolean controls"""
        for var_name in self.control_vars:
            self.ai_core.update_control_setting(var_name, True)
        self.update_control_display()
        self.log_system_message("All controls enabled")

    def disable_all_controls(self):
        """Disable all boolean controls"""
        for var_name in self.control_vars:
            self.ai_core.update_control_setting(var_name, False)
        self.update_control_display()
        self.log_system_message("All controls disabled")

    def reset_controls(self):
        """Reset controls to defaults"""
        self.control_manager.reset_to_defaults()
        self.update_control_display()
        self.log_system_message("Controls reset to defaults")

    def manual_summarize(self):
        """Trigger manual memory summarization for past days"""
        try:
            success = self.ai_core.manual_summarize_past_days()
            if success:
                self.log_system_message("Manual summarization of past days completed successfully")
            else:
                self.log_system_message("Manual summarization completed but no new summaries were created")
        except Exception as e:
            self.log_system_message(f"Manual summarization failed: {e}")

    def force_cleanup(self):
        """Force memory cleanup - summarize all past day entries"""
        try:
            success = self.ai_core.force_memory_cleanup()
            if success:
                self.log_system_message("Force memory cleanup completed successfully - all past days summarized")
            else:
                self.log_system_message("Force memory cleanup completed but no summaries were created")
        except Exception as e:
            self.log_system_message(f"Force memory cleanup failed: {e}")

    def show_memory_debug(self):
        """Show memory debug information in a popup - updated for day-based system"""
        try:
            debug_info = self.ai_core.get_memory_debug_info()
            
            # Create debug window
            debug_window = tk.Toplevel()
            debug_window.title("Memory Debug Information - Day-Based System")
            debug_window.configure(bg=DarkTheme.BG_DARK)
            debug_window.geometry("700x600")
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(debug_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(
                text_frame,
                wrap=tk.WORD,
                font=("Consolas", 10),
                bg=DarkTheme.BG_DARKER,
                fg=DarkTheme.FG_PRIMARY,
                insertbackground=DarkTheme.FG_PRIMARY
            )
            
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side="left", fill=tk.BOTH, expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Format and insert debug info
            debug_text = "MEMORY DEBUG INFORMATION - DAY-BASED SYSTEM\n"
            debug_text += "=" * 50 + "\n\n"
            
            if 'error' in debug_info:
                debug_text += f"ERROR: {debug_info['error']}\n"
            else:
                debug_text += f"Memory Statistics:\n"
                for key, value in debug_info.get('memory_stats', {}).items():
                    debug_text += f"  {key}: {value}\n"
                
                debug_text += f"\nDay-Based Memory Breakdown:\n"
                debug_text += f"  Current day entries: {debug_info.get('current_day_entry_count', 'N/A')}\n"
                debug_text += f"  Past day unsummarized entries: {debug_info.get('past_day_entry_count', 'N/A')}\n"
                debug_text += f"  Summarization candidate days: {debug_info.get('summarization_candidate_days', [])}\n"
                
                debug_text += f"\nFile System Status:\n"
                debug_text += f"  Memory file exists: {debug_info.get('memory_file_exists', 'N/A')}\n"
                debug_text += f"  Embeddings file exists: {debug_info.get('embeddings_file_exists', 'N/A')}\n"
                debug_text += f"  Base memory directory exists: {debug_info.get('base_memory_dir_exists', 'N/A')}\n"
                
                debug_text += f"\nInteraction Tracking:\n"
                debug_text += f"  Total interactions: {debug_info.get('interaction_count', 'N/A')}\n"
                debug_text += f"  Last summarization at interaction: {debug_info.get('last_summarization', 'N/A')}\n"
                debug_text += f"  Interactions since last summary: {debug_info.get('interactions_since_last_summary', 'N/A')}\n"
                debug_text += f"  Auto summary threshold: {debug_info.get('auto_summary_threshold', 'N/A')}\n"
                
                debug_text += f"\nMemory System Explanation:\n"
                debug_text += f"- Current day entries: Stored in memory.json, used for short-term context\n"
                debug_text += f"- Past day entries: Older entries awaiting summarization\n"
                debug_text += f"- Daily summaries: Compressed summaries of past days stored as embeddings\n"
                debug_text += f"- Base knowledge: Static knowledge base from text files\n"
                debug_text += f"- Auto-summarization triggers every {debug_info.get('auto_summary_threshold', 'N/A')} interactions\n"
            
            text_widget.insert(tk.END, debug_text)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_system_message(f"Failed to show memory debug info: {e}")

    def check_warudo_status(self):
        """Check Warudo connection status"""
        try:
            warudo_manager = getattr(self.ai_core, 'warudo_manager', None)
            if warudo_manager:
                connected = warudo_manager.controller.ws_connected if warudo_manager.controller else False
                enabled = warudo_manager.enabled
                
                status_text = f"Connected: {'Yes' if connected else 'No'}, Enabled: {'Yes' if enabled else 'No'}"
                status_color = DarkTheme.ACCENT_GREEN if connected and enabled else DarkTheme.ACCENT_RED
                
                self.warudo_status_label.config(
                    text=f"Status: {status_text}",
                    foreground=status_color
                )
                
                self.log_system_message(f"Warudo status: {status_text}")
            else:
                self.warudo_status_label.config(
                    text="Status: Not Available",
                    foreground=DarkTheme.ACCENT_RED
                )
                self.log_system_message("Warudo manager not available")
                
        except Exception as e:
            self.log_system_message(f"Error checking Warudo status: {e}")

    def toggle_control(self, var_name):
        """Toggle a control setting using the control manager"""
        new_value = self.ai_core.toggle_control_setting(var_name)
        if new_value is not None:
            # Update the GUI checkbox
            self.control_vars[var_name].set(new_value)
            # Update status label
            self.status_labels[var_name].config(
                text=f"({'ON' if new_value else 'OFF'})",
                foreground=DarkTheme.ACCENT_GREEN if new_value else DarkTheme.FG_MUTED
            )
            
            # Special handling for certain controls
            if var_name == "PLAYING_MINECRAFT" and new_value:
                self.log_system_message("Minecraft mode enabled - bot will use environmental data and integrated controls")
            elif var_name == "USE_VISION" and new_value:
                self.log_system_message("Vision enabled - bot can analyze screenshots")
            elif var_name == "USE_SEARCH" and new_value:
                self.log_system_message("Web search enabled - bot can search internet")
            elif var_name == "USE_LONG_MEMORY" and new_value:
                self.log_system_message("Long memory search enabled - bot will search daily summaries and base knowledge")
            elif var_name == "SAVE_MEMORY" and new_value:
                self.log_system_message("Memory saving enabled - conversations will be saved to day-based system")
        else:
            self.log_system_message(f"Failed to toggle control: {var_name}")

    def update_control_display(self):
        """Update all control displays to reflect current values"""
        for var_name, bool_var in self.control_vars.items():
            current_value = getattr(controls, var_name, False)
            bool_var.set(current_value)
            if var_name in self.status_labels:
                self.status_labels[var_name].config(
                    text=f"({'ON' if current_value else 'OFF'})",
                    foreground=DarkTheme.ACCENT_GREEN if current_value else DarkTheme.FG_MUTED
                )