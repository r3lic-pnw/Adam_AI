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
import numpy as np

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
        self.root.geometry("1600x1000")
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
        self.recognizer = None
        self.stream = None
        self.control_vars = {}
        self.input_queue = queue.Queue()
        self.current_message = None
        self.status_labels = {}
        self.voice_thread = None
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
        """Create comprehensive control panel with all boolean variables from controls.py"""
        
        # Create scrollable frame for controls
        control_canvas = tk.Canvas(self.left_frame, bg=DarkTheme.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=control_canvas.yview)
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
        
        # Define control groups with all variables from controls.py
        control_groups = {
            "AI Capabilities": [
                ("Web Search", "USE_SEARCH", "Enable web search functionality"),
                ("Computer Vision", "USE_VISION", "Enable computer vision/screenshot analysis"),
                ("Base Memory", "USE_BASE_MEMORY", "Enable base memory system"),
                ("Memory Search", "USE_MEMORY_SEARCH", "Enable enhanced memory search"),
            ],
            "Game Integration": [
                ("Playing Game (Legacy)", "PLAYING_GAME", "Legacy flag for game integration"),
                ("Minecraft Mode", "PLAYING_MINECRAFT", "Enable Minecraft bot integration"),
                ("Group Chat Mode", "IN_GROUP_CHAT", "Enable group chat conversation mode"),
            ],
            "Prompt Components": [
                ("System Prompt", "INCLUDE_SYSTEM_PROMPT", "Include system/personality prompt"),
                ("Vision Results", "INCLUDE_VISION_RESULTS", "Include vision analysis in prompt"),
                ("Search Results", "INCLUDE_SEARCH_RESULTS", "Include web search results in prompt"),
                ("Tool Metadata", "INCLUDE_TOOL_METADATA", "Include execution metadata"),
                ("Chat History", "INCLUDE_CHAT_HISTORY", "Include recent conversation history"),
                ("Memory Context", "INCLUDE_MEMORY_CONTEXT", "Include relevant memory context"),
                ("Enhanced Memory", "INCLUDE_ENHANCED_MEMORY", "Include enhanced memory search"),
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
                ("Save Memory", "SAVE_MEMORY", "Save conversations to memory system"),
            ]
        }
        
        # Create control sections
        for group_name, controls_list in control_groups.items():
            self.create_control_group(scrollable_frame, group_name, controls_list)
        
        # Add preset buttons
        preset_frame = ttk.LabelFrame(scrollable_frame, text="Quick Presets", style="Dark.TLabelframe")
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(preset_buttons_frame, text="Minimal", 
                   command=lambda: self.load_preset("minimal"), width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Standard", 
                   command=lambda: self.load_preset("standard"), width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_buttons_frame, text="Debug", 
                   command=lambda: self.load_preset("debug"), width=12).pack(side=tk.LEFT, padx=2)
        
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
        voice_frame = ttk.LabelFrame(self.center_frame, text="Voice Control", style="Dark.TLabelframe")
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
            self.voice_button.config(text="Start Voice Input")
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
            
            # Count enabled controls
            enabled_controls = sum(1 for var_name in self.control_vars 
                                 if getattr(controls, var_name, False))
            total_controls = len(self.control_vars)
            
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
Voice: {'ON' if self.voice_enabled else 'OFF'}
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
    
    def voice_processing_loop(self):
        """Process voice input in a background thread - Fixed version"""
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