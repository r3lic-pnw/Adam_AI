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
import sounddevice as sd
from vosk import Model, KaldiRecognizer
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
    from BASE.tools.voice_to_text import load_vosk_model
    from BASE.tools.text_to_voice import speak_through_vbcable
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the correct directory structure")
    sys.exit(1)

class DarkTheme:
    LABEL = "#ffffff"
    BG_DARK = "#2b2b2b"
    BG_DARKER = "#1e1e1e"
    BG_LIGHTER = "#3c3c3c"
    FG_PRIMARY = "#FFFFFF"
    FG_SECONDARY = "#7e7e7e"
    FG_MUTED = "#C90000"
    ACCENT_BLUE = "#00ff15"
    ACCENT_GREEN = "#fbff00"
    ACCENT_ORANGE = "#fb923c"
    ACCENT_RED = "#ef4444"
    ACCENT_YELLOW = "#fbbf24"
    BORDER = "#000000"

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
        self.root.geometry("1400x900")
        self.apply_dark_theme()
        self.config = Config()
        self.ai_core = AICore(self.config, controls)
        self.control_manager = self.ai_core.get_control_manager()
        self.message_queue = queue.Queue()
        self.system_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.raw_queue = queue.Queue()
        self.processing = False
        self.voice_enabled = False
        self.audio_started = False
        self.speaking_thread = None
        self.vosk_model = None
        self.stream = None
        self.control_vars = {}
        self.input_queue = queue.Queue()
        self.current_message = None
        self.status_labels = {}
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = CustomWriter(self.system_queue, self.original_stdout, self.ansi_escape)
        sys.stderr = CustomWriter(self.system_queue, self.original_stderr, self.ansi_escape)
        self.setup_gui()
        self.create_menu()
        self.start_queue_processor()
        self.log_system_message("GUI initialized successfully")

    def apply_dark_theme(self):
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
            self.update_control_display()
            self.log_system_message(f"Loaded preset: {preset_name}")
            messagebox.showinfo("Preset Loaded", f"Successfully loaded '{preset_name}' preset")
        else:
            messagebox.showerror("Error", f"Failed to load preset: {preset_name}")

    def reset_controls(self):
        """Reset controls to defaults"""
        if messagebox.askyesno("Reset Controls", "Reset all controls to default values?"):
            self.control_manager.reset_to_defaults()
            self.update_control_display()
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
        self.create_main_frames()
        self.create_system_panel()
        self.create_chat_panel()
        self.create_control_panel()
        self.create_input_panel()

    def create_main_frames(self):
        self.left_frame = ttk.Frame(self.root, width=450)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        self.left_frame.pack_propagate(False)
        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_system_panel(self):
        system_frame = ttk.LabelFrame(self.left_frame, text="System Information", style="Dark.TLabelframe")
        system_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.system_log = scrolledtext.ScrolledText(
            system_frame,
            height=12,
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
        stats_frame = ttk.Frame(system_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.stats_label = tk.Label(stats_frame, text="Loading stats...", 
                                   font=("Consolas", 9), foreground=DarkTheme.FG_SECONDARY,
                                   background=DarkTheme.BG_DARK)
        self.stats_label.pack(anchor=tk.W)
        voice_frame = ttk.Frame(system_frame)
        voice_frame.pack(fill=tk.X, padx=5, pady=(5, 5))
        self.voice_button = ttk.Button(
            voice_frame,
            text="Start Voice Input",
            command=self.toggle_voice_input,
            width=20
        )
        self.voice_button.pack(side=tk.LEFT, padx=(0, 10))
        self.voice_status = tk.Label(
            voice_frame,
            text="Voice: Disabled",
            font=("Arial", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARK
        )
        self.voice_status.pack(side=tk.LEFT)
        self.update_stats()

    def create_chat_panel(self):
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
        self.chat_display.tag_configure("user", foreground=DarkTheme.ACCENT_BLUE, font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("bot", foreground=DarkTheme.ACCENT_ORANGE, font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("system", foreground=DarkTheme.FG_MUTED, font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_configure("error", foreground=DarkTheme.ACCENT_RED, font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("voice", foreground=DarkTheme.ACCENT_GREEN, font=("Segoe UI", 10, "italic"))

    def create_control_panel(self):
        control_frame = ttk.LabelFrame(self.left_frame, text="AI Controls", style="Dark.TLabelframe")
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Main controls
        main_controls = [
            ("Vision", "USE_VISION"),
            ("Search", "USE_SEARCH"),
            ("Memory Search", "USE_MEMORY_SEARCH"),
            ("Minecraft Mode", "PLAYING_MINECRAFT"),
            ("Group Chat", "IN_GROUP_CHAT"),
            ("Animations", "AVATAR_ANIMATIONS"),
            ("Speech", "AVATAR_SPEECH"),
            ("Save Memory", "SAVE_MEMORY"),
        ]
        
        for display_name, var_name in main_controls:
            frame = ttk.Frame(control_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            current_value = getattr(controls, var_name, False)
            bool_var = tk.BooleanVar(value=current_value)
            self.control_vars[var_name] = bool_var
            checkbox = ttk.Checkbutton(
                frame,
                text=display_name,
                variable=bool_var,
                command=lambda vn=var_name: self.toggle_control(vn)
            )
            checkbox.pack(side=tk.LEFT)
            status_color = DarkTheme.ACCENT_GREEN if current_value else DarkTheme.FG_MUTED
            status_label = tk.Label(frame, text=f"({'ON' if current_value else 'OFF'})", 
                                   font=("Arial", 8), foreground=status_color,
                                   background=DarkTheme.BG_DARK)
            status_label.pack(side=tk.RIGHT)
            self.status_labels[var_name] = status_label

        # Logging controls
        log_frame = ttk.LabelFrame(control_frame, text="Logging", style="Dark.TLabelframe")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        log_configs = [
            ("Tool Execution", "LOG_TOOL_EXECUTION"),
            ("Prompt Construction", "LOG_PROMPT_CONSTRUCTION"),
            ("Response Processing", "LOG_RESPONSE_PROCESSING"),
        ]
        for display_name, var_name in log_configs:
            frame = ttk.Frame(log_frame)
            frame.pack(fill=tk.X, padx=5, pady=1)
            current_value = getattr(controls, var_name, False)
            bool_var = tk.BooleanVar(value=current_value)
            self.control_vars[var_name] = bool_var
            checkbox = ttk.Checkbutton(
                frame,
                text=display_name,
                variable=bool_var,
                command=lambda vn=var_name: self.toggle_control(vn)
            )
            checkbox.pack(side=tk.LEFT)
            status_color = DarkTheme.ACCENT_GREEN if current_value else DarkTheme.FG_MUTED
            status_label = tk.Label(frame, text=f"({'ON' if current_value else 'OFF'})", 
                                   font=("Arial", 8), foreground=status_color,
                                   background=DarkTheme.BG_DARK)
            status_label.pack(side=tk.RIGHT)
            self.status_labels[var_name] = status_label

        # Quick preset buttons
        preset_frame = ttk.Frame(control_frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(preset_frame, text="Minimal", command=lambda: self.load_preset("minimal")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Standard", command=lambda: self.load_preset("standard")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Debug", command=lambda: self.load_preset("debug")).pack(side=tk.LEFT, padx=2)

    def create_input_panel(self):
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
    
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        if not self.voice_enabled:
            try:
                self.log_system_message("Initializing voice input...")
                self.init_audio()
                self.start_vosk_stream()
                self.voice_enabled = True
                self.voice_button.config(text="Stop Voice Input")
                self.voice_status.config(text="Voice: Listening...", foreground=DarkTheme.ACCENT_GREEN)
                self.log_system_message("Voice input started successfully")
                
                # Start voice processing thread
                threading.Thread(target=self.voice_processing_loop, daemon=True).start()
                
            except Exception as e:
                self.log_system_message(f"Failed to start voice input: {str(e)}")
                messagebox.showerror("Voice Error", f"Failed to initialize voice input: {str(e)}")
        else:
            self.stop_voice_input()
    
    def stop_voice_input(self):
        """Stop voice input"""
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.voice_enabled = False
            self.voice_button.config(text="Start Voice Input")
            self.voice_status.config(text="Voice: Disabled", foreground=DarkTheme.FG_MUTED)
            self.log_system_message("Voice input stopped")
        except Exception as e:
            self.log_system_message(f"Error stopping voice input: {str(e)}")
    
    def init_audio(self):
        """Initialize audio for voice input"""
        self.vosk_model = load_vosk_model()
    
    def start_vosk_stream(self):
        """Start Vosk audio stream"""
        def recognition_worker():
            rec = KaldiRecognizer(self.vosk_model, 16000)
            while True:
                data = self.raw_queue.get()
                if data == b"__EXIT__":
                    break
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if len(text) >= 5 and f"{botname}".lower() not in text.lower():
                        self.text_queue.put(text)
                        print(f"[Speech] Recognized: {text}")

        threading.Thread(target=recognition_worker, daemon=True).start()
        
        self.stream = sd.RawInputStream(
            samplerate=16000,
            blocksize=4096,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        )
        self.stream.start()
        print("[Listener] Audio stream started.")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Audio callback function to queue raw audio data"""
        if status:
            print(f"[Audio status]: {status}")
        self.raw_queue.put(bytes(indata))
    
    def voice_processing_loop(self):
        """Process voice input in background thread"""
        while self.voice_enabled:
            try:
                texts = []
                while not self.text_queue.empty():
                    try:
                        text = self.text_queue.get(timeout=0.05)
                        if text and text.strip():
                            texts.append(text)
                    except queue.Empty:
                        pass
                
                if texts:
                    combined_text = " ".join(texts).strip()
                    if combined_text:
                        self.add_chat_message(f"{username} (Voice)", combined_text, "voice_input")
                        self.input_queue.put(combined_text)
                
                time.sleep(0.1)
                
            except Exception as e:
                self.log_system_message(f"Voice processing error: {str(e)}")
                time.sleep(1)
    
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
            self.log_system_message(f"Control {var_name}: {'ON' if new_value else 'OFF'}")
            
            # Special handling for certain controls
            if var_name == "PLAYING_MINECRAFT" and new_value:
                self.log_system_message("Minecraft mode enabled - bot will use environmental data")
            elif var_name == "USE_VISION" and new_value:
                self.log_system_message("Vision enabled - bot can analyze screenshots")
            elif var_name == "USE_SEARCH" and new_value:
                self.log_system_message("Web search enabled - bot can search internet")
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
    
    def log_system_message(self, message):
        """Add message to system log"""
        self.system_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.system_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.system_log.see(tk.END)
        self.system_log.config(state=tk.DISABLED)
    
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
            
            stats_text = f"""Memory: {memory_stats['memory_entries']} entries
Summaries: {memory_stats['summary_embeddings_count']}
Base: {memory_stats['base_embeddings_count']}
Interactions: {self.ai_core.interaction_count}

Model: {self.config.text_llm_model}
Vision: {self.config.vision_llm_model}
Endpoint: {self.config.ollama_endpoint}

Voice: {'ON' if self.voice_enabled else 'OFF'}
Vision: {'ON' if controls.USE_VISION else 'OFF'}
Search: {'ON' if controls.USE_SEARCH else 'OFF'}
Minecraft: {'ON' if controls.PLAYING_MINECRAFT else 'OFF'}

Current Preset: {self.get_current_preset_guess()}"""
            
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
            if self.voice_enabled:
                self.stop_voice_input()
            
            # Stop any speaking threads
            if self.speaking_thread and self.speaking_thread.is_alive():
                self.speaking_thread.join(timeout=1.0)
            
            # Signal audio threads to exit
            try:
                self.raw_queue.put(b"__EXIT__")
            except:
                pass
            
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = OllamaGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()