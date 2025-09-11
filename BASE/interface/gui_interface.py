# Filename: gui_interface.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Menu
import threading
import queue
import time
import json
import sys
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from BASE.core.ai_core import AICore
    from BASE.core.config import Config
    from BASE.core.control_methods import ControlManager
    from personality.bot_info import botname, username
    from personality import controls
    from BASE.tools.text_to_voice import speak_through_vbcable
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the correct directory structure")
    sys.exit(1)

try:
    from BASE.tools.animate import WarudoManager, WEBSOCKET_AVAILABLE
except Exception as e:
    WarudoManager = None
    WEBSOCKET_AVAILABLE = False
    print(f"Warning: Could not import WarudoManager: {e}")

from gui_themes import DarkTheme
from gui_components import VoiceManager, ControlPanelManager

class CustomWriter:
    def __init__(self, queue, original, ansi_escape):
        self.queue = queue
        self.original = original
        self.ansi_escape = ansi_escape

    def write(self, text):
        self.original.write(text)
        clean_text = self.ansi_escape.sub('', text).strip()
        if clean_text:
            self.queue.put(clean_text)

    def flush(self):
        self.original.flush()

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{botname} - Ollama Agent GUI")
        self.root.geometry("1600x1000")
        
        # Initialize core components
        self.config = Config()
        self.ai_core = AICore(self.config, controls)
        self.control_manager = self.ai_core.get_control_manager()
        
        # Initialize queues and threading
        self.message_queue = queue.Queue()
        self.system_queue = queue.Queue()
        self.input_queue = queue.Queue()
        self.processing = False
        self.current_message = None
        self.speaking_thread = None
        
        # Initialize regex for ANSI escape sequences
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        # Redirect stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = CustomWriter(self.system_queue, self.original_stdout, self.ansi_escape)
        sys.stderr = CustomWriter(self.system_queue, self.original_stderr, self.ansi_escape)
        
        # Initialize component managers
        self.voice_manager = VoiceManager(self.message_queue, self.input_queue, self.log_system_message)
        self.control_panel_manager = ControlPanelManager(self.ai_core, self.control_manager, self.log_system_message)
        
        self.warudo = None
        if WarudoManager and WEBSOCKET_AVAILABLE:
            try:
                # adjust URL if your Warudo uses a different host/port
                self.warudo = WarudoManager("ws://127.0.0.1:19190", auto_connect=True, timeout=2.0)
                if self.warudo and getattr(self.warudo, "controller", None) and not self.warudo.controller.ws_connected:
                    self.log_system_message("Warudo available but not connected (attempted quick connect).")
                else:
                    self.log_system_message("Warudo manager initialized and connected.")
            except Exception as e:
                self.warudo = None
                self.log_system_message(f"Failed to initialize Warudo manager: {e}")
        else:
            self.log_system_message("Warudo manager unavailable (websocket-client not installed or animate.py missing).")

        # Apply theme and setup GUI
        self.apply_dark_theme()
        self.setup_gui()
        self.create_menu()
        self.start_queue_processor()
        self.log_system_message("GUI initialized successfully")

    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.root.configure(bg=DarkTheme.BG_DARK)
        style = ttk.Style()
        style.theme_use('clam')

        # General widget styling
        style.configure('TFrame', background=DarkTheme.BG_DARK)
        style.configure('TLabel', background=DarkTheme.BG_DARK, foreground=DarkTheme.FG_PRIMARY)
        style.configure('TButton', background=DarkTheme.BG_LIGHTER, foreground=DarkTheme.FG_PRIMARY,
                       borderwidth=1, focuscolor='none')
        style.map('TButton',
                 background=[('active', DarkTheme.ACCENT_BLUE),
                           ('pressed', DarkTheme.BG_DARKER)])
        style.configure('TCheckbutton', background=DarkTheme.BG_DARK, foreground=DarkTheme.FG_PRIMARY,
                       focuscolor='none')
        style.map('TCheckbutton',
                 background=[('active', DarkTheme.BG_DARK)],
                 foreground=[('active', DarkTheme.FG_PRIMARY)])

        # Custom dark LabelFrame with black borders
        style.element_create("DarkFrame.border", "from", "clam")
        style.layout("Dark.TLabelframe",
                     [('DarkFrame.border', {'sticky': 'nswe', 'border': '1', 'children':
                         [('Labelframe.padding', {'sticky': 'nswe', 'children':
                             [('Labelframe.label', {'sticky': ''}),
                              ('Labelframe.frame', {'sticky': 'nswe'})]
                         })]
                     })])
        style.configure("Dark.TLabelframe", background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY, bordercolor=DarkTheme.BORDER)
        style.configure("Dark.TLabelframe.Label", background=DarkTheme.BG_DARK,
                        foreground=DarkTheme.FG_PRIMARY)

    def create_menu(self):
        """Create menu bar with control options"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Controls menu
        controls_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Controls", menu=controls_menu)
        
        # Presets submenu
        presets_menu = Menu(controls_menu, tearoff=0)
        controls_menu.add_cascade(label="Load Preset", menu=presets_menu)
        
        for preset in self.control_manager.get_available_presets():
            presets_menu.add_command(
                label=preset.replace('_', ' ').title(),
                command=lambda p=preset: self.load_preset(p)
            )
        
        controls_menu.add_separator()
        controls_menu.add_command(label="Reset to Defaults", command=self.reset_controls)
        controls_menu.add_command(label="Show Status", command=self.show_status_dialog)
        controls_menu.add_separator()
        controls_menu.add_command(label="Validate Configuration", command=self.validate_config)
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clear Chat", command=self.clear_chat)
        tools_menu.add_command(label="Export Settings", command=self.export_settings)

    def load_preset(self, preset_name):
        """Load a control preset"""
        success = self.control_manager.load_preset(preset_name)
        if success:
            self.control_panel_manager.update_control_display()
            self.log_system_message(f"Loaded preset: {preset_name}")
            messagebox.showinfo("Preset Loaded", f"Successfully loaded '{preset_name}' preset")
        else:
            messagebox.showerror("Error", f"Failed to load preset: {preset_name}")

    def reset_controls(self):
        """Reset controls to defaults"""
        if messagebox.askyesno("Reset Controls", "Reset all controls to default values?"):
            self.control_manager.reset_to_defaults()
            self.control_panel_manager.update_control_display()
            self.log_system_message("Controls reset to defaults")

    def show_status_dialog(self):
        """Show current status in a dialog"""
        status = self.control_manager.get_status_summary()
        dialog = tk.Toplevel(self.root)
        dialog.title("Current Status")
        dialog.configure(bg=DarkTheme.BG_DARK)
        dialog.geometry("500x400")
        
        text_widget = scrolledtext.ScrolledText(
            dialog,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=DarkTheme.BG_DARKER,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, status)
        text_widget.config(state=tk.DISABLED)

    def validate_config(self):
        """Validate current configuration"""
        is_valid = self.control_manager.validate_all_configs()
        if is_valid:
            messagebox.showinfo("Validation", "Configuration is valid!")
        else:
            messagebox.showwarning("Validation", "Configuration has issues. Check system log for details.")

    def export_settings(self):
        """Export current settings to a file"""
        try:
            settings = self.control_manager.get_all_features()
            filename = f"ai_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Export", f"Settings exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export settings: {e}")

    def setup_gui(self):
        """Setup the main GUI layout"""
        self.create_main_frames()
        self.create_control_panel()
        self.create_system_panel()
        self.create_chat_panel()

    def create_main_frames(self):
        """Create the main layout frames: left (controls), center (system), right (chat)"""
        # Left frame for controls
        self.left_frame = ttk.Frame(self.root, width=400)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.left_frame.pack_propagate(False)
        
        # Center frame for system information
        self.center_frame = ttk.Frame(self.root, width=450)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.center_frame.pack_propagate(False)
        
        # Right frame for chat
        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_control_panel(self):
        """Create control panel using the control panel manager"""
        self.control_panel_manager.create_control_panel(self.left_frame)

    def create_system_panel(self):
        """Create system information panel in center column"""
        # System log
        system_frame = ttk.LabelFrame(self.center_frame, text="System Information", style="Dark.TLabelframe")
        system_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.system_log = scrolledtext.ScrolledText(
            system_frame,
            height=20,
            width=50,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARKER,
            fg=DarkTheme.ACCENT_GREEN,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_BLUE,
            selectforeground=DarkTheme.FG_PRIMARY
        )
        self.system_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics panel
        stats_frame = ttk.LabelFrame(self.center_frame, text="Statistics", style="Dark.TLabelframe")
        stats_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.stats_label = tk.Label(
            stats_frame, 
            text="Loading stats...", 
            font=("Consolas", 9), 
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARK,
            justify=tk.LEFT,
            anchor="w"
        )
        self.stats_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Voice control panel
        self.voice_manager.create_voice_panel(self.center_frame)
        
        self.update_stats()

    def create_chat_panel(self):
        """Create chat panel in right column"""
        chat_frame = ttk.LabelFrame(self.right_frame, text=f"Chat with {botname}", style="Dark.TLabelframe")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            bg=DarkTheme.BG_DARKER,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_BLUE,
            selectforeground=DarkTheme.FG_PRIMARY
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags
        self.chat_display.tag_configure("user", foreground=DarkTheme.ACCENT_BLUE, font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("bot", foreground=DarkTheme.ACCENT_ORANGE, font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("system", foreground=DarkTheme.FG_MUTED, font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_configure("error", foreground=DarkTheme.ACCENT_RED, font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("voice", foreground=DarkTheme.ACCENT_GREEN, font=("Segoe UI", 10, "italic"))
        
        # Input panel
        self.create_input_panel()

    def create_input_panel(self):
        """Create input panel for chat"""
        input_frame = ttk.Frame(self.right_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.input_text = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=DarkTheme.BG_LIGHTER,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_BLUE,
            selectforeground=DarkTheme.FG_PRIMARY,
            borderwidth=1,
            relief="solid"
        )
        self.input_text.pack(fill=tk.X, padx=(0, 5), pady=(0, 5), side=tk.LEFT, expand=True)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.send_button = ttk.Button(
            button_frame,
            text="Send",
            command=self.send_message,
            width=12
        )
        self.send_button.pack(pady=(0, 5))
        
        clear_button = ttk.Button(
            button_frame,
            text="Clear Chat",
            command=self.clear_chat,
            width=12
        )
        clear_button.pack(pady=(0, 5))
        
        self.processing_label = tk.Label(
            button_frame,
            text="",
            font=("Arial", 9),
            foreground=DarkTheme.ACCENT_YELLOW,
            background=DarkTheme.BG_DARK
        )
        self.processing_label.pack(pady=(5, 0))
        
        self.input_text.bind("<Control-Return>", lambda e: self.send_message())
        self.input_text.bind("<Return>", self.handle_return)
        
    def handle_return(self, event):
        """Handle Return key press"""
        if event.state & 0x1:  # Shift key
            return None
        else:
            self.send_message()
            return "break"
    
    def send_message(self):
        """Send message to AI"""
        message = self.input_text.get("1.0", tk.END).strip()
        
        if not message:
            return
        
        # Clear input
        self.input_text.delete("1.0", tk.END)
        
        # Display user message immediately
        self.add_chat_message(f"{username}", message, "user")
        
        # Queue for processing
        self.input_queue.put(message)
    
    def process_message(self, message):
        """Process message in background thread"""
        try:
            import asyncio
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Generate response
            response = loop.run_until_complete(self.ai_core.generate_response(message))
            
            if response:
                # Queue the response for GUI thread
                self.message_queue.put(("bot", botname, response))

                try:
                    if getattr(self, 'warudo', None):
                        # run detection in a separate thread so it doesn't block the loop
                        threading.Thread(target=self.warudo.detect_and_send_animations, args=(response,), daemon=True).start()
                except Exception as e:
                    self.message_queue.put(("system", None, f"Warudo error: {e}"))
                
                # Handle text-to-speech if enabled
                if controls.AVATAR_SPEECH and len(response) < 600:
                    self.message_queue.put(("system", None, "Initiating text-to-speech..."))
                    self.speaking_thread = threading.Thread(
                        target=speak_through_vbcable, args=(response,), daemon=True
                    )
                    self.speaking_thread.start()
                elif len(response) >= 600:
                    self.message_queue.put(("system", None, "Reply too long for speech (over 600 chars). Text only."))
            else:
                self.message_queue.put(("error", "System", "No response generated"))
                
        except Exception as e:
            self.message_queue.put(("error", "Error", f"Failed to process message: {str(e)}"))
            import traceback
            traceback.print_exc()
        finally:
            # Signal processing complete
            self.message_queue.put(("processing_complete", None, None))
            self.current_message = None
    
    def add_chat_message(self, sender, message, msg_type="user"):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add message with appropriate formatting
        if msg_type == "system":
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, f"{message}\n", "system")
        elif msg_type == "error":
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "error")
            self.chat_display.insert(tk.END, f"{sender}: {message}\n", "error")
        elif msg_type == "voice_input":
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, f"{sender}: ", "voice")
            self.chat_display.insert(tk.END, f"{message}\n\n")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, f"{sender}: ", msg_type)
            self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def log_system_message(self, message: str):
        """Log system messages into the system_log widget."""
        try:
            self.system_log.config(state=tk.NORMAL)
            self.system_log.insert(tk.END, f"[System] {message}\n")
            self.system_log.config(state=tk.DISABLED)
            self.system_log.yview(tk.END)
        except Exception as e:
            # fallback if system_log is not available
            print(f"[System] {message} (log_system_message fallback: {e})")

    
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.log_system_message("Chat cleared")
    
    def update_stats(self):
        """Update system statistics"""
        try:
            memory_stats = self.ai_core.memory_manager.get_memory_stats()
            
            # Count enabled controls
            enabled_controls = sum(1 for var_name in self.control_panel_manager.control_vars 
                                 if getattr(controls, var_name, False))
            total_controls = len(self.control_panel_manager.control_vars)
            
            stats_text = f"""System Status:
Memory: {memory_stats['memory_entries']} entries
Summaries: {memory_stats['summary_embeddings_count']}
Base: {memory_stats['base_embeddings_count']}
Interactions: {self.ai_core.interaction_count}

Configuration:
Model: {self.config.text_llm_model}
Vision: {self.config.vision_llm_model}
Endpoint: {self.config.ollama_endpoint}

Controls Active: {enabled_controls}/{total_controls}
Voice: {'ON' if self.voice_manager.voice_enabled else 'OFF'}
Preset: {self.get_current_preset_guess()}

Key Features:
Vision: {'ON' if controls.USE_VISION else 'OFF'}
Search: {'ON' if controls.USE_SEARCH else 'OFF'}
Memory: {'ON' if controls.USE_MEMORY_SEARCH else 'OFF'}
Minecraft: {'ON' if controls.PLAYING_MINECRAFT else 'OFF'}
Speech: {'ON' if controls.AVATAR_SPEECH else 'OFF'}"""
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"Error loading stats: {str(e)}")
        
        # Schedule next update
        self.root.after(5000, self.update_stats)

    def get_current_preset_guess(self):
        """Try to guess current preset based on settings"""
        current_settings = self.control_manager.get_all_features()
        
        # Check against known presets
        presets = {
            'minimal': {
                'USE_SEARCH': False,
                'USE_VISION': False,
                'USE_MEMORY_SEARCH': False,
                'SAVE_MEMORY': False,
            },
            'standard': {
                'USE_SEARCH': True,
                'USE_VISION': True,
                'USE_MEMORY_SEARCH': True,
                'SAVE_MEMORY': True,
            },
            'minecraft': {
                'PLAYING_MINECRAFT': True,
                'USE_VISION': True,
            },
            'debug': {
                'LOG_TOOL_EXECUTION': True,
                'LOG_PROMPT_CONSTRUCTION': True,
            }
        }
        
        for preset_name, preset_settings in presets.items():
            if all(current_settings.get(key) == value for key, value in preset_settings.items()):
                return preset_name
        
        return "Custom"
    
    def start_queue_processor(self):
        """Start processing queued messages"""
        self.process_queues()
    
    def process_queues(self):
        """Process messages from background threads"""
        try:
            # Process chat messages
            while not self.message_queue.empty():
                try:
                    msg_type, sender, message = self.message_queue.get_nowait()
                    
                    if msg_type == "processing_complete":
                        self.processing = False
                        self.send_button.config(state=tk.NORMAL)
                        self.processing_label.config(text="")
                        self.current_message = None
                    elif msg_type == "voice_input":
                        self.add_chat_message(sender, message, "voice_input")
                    elif msg_type == "system":
                        if message:
                            self.log_system_message(message)
                    else:
                        self.add_chat_message(sender, message, msg_type)
                        
                except queue.Empty:
                    break
            
            # Process system messages
            while not self.system_queue.empty():
                try:
                    message = self.system_queue.get_nowait()
                    self.log_system_message(message)
                except queue.Empty:
                    break
                    
            # Process next input from queue if ready
            if not self.processing and not self.input_queue.empty():
                combined = []
                while not self.input_queue.empty():
                    combined.append(self.input_queue.get())
                combined_message = " ".join(combined)
                self.current_message = combined_message
                self.processing = True
                self.send_button.config(state=tk.DISABLED)
                self.processing_label.config(text="Processing...")
                threading.Thread(target=self.process_message, args=(self.current_message,), daemon=True).start()
                
        except Exception as e:
            print(f"Error processing queues: {e}")
        
        # Schedule next check
        self.root.after(100, self.process_queues)

    def on_closing(self):
        """Handle window closing"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        try:
            self.voice_manager.stop_voice_input()
            
            # Stop any speaking threads
            if self.speaking_thread and self.speaking_thread.is_alive():
                self.speaking_thread.join(timeout=1.0)
            
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.root.destroy()

intro = """
Begin chatting here.
"""

def main():
    try:
        root = tk.Tk()
        app = OllamaGUI(root)
        app.add_chat_message("System", intro)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()