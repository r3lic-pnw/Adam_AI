# Filename: personality/controls.py
"""
Dynamic control variables for AI functionality.
These variables can be modified at runtime to enable/disable features.
Control methods are available in BASE.core.control_methods
"""

# === AI CAPABILITIES ===
# Core tool usage flags
USE_SEARCH = False              # Enable web search functionality
USE_VISION = False              # Enable computer vision/screenshot analysis
USE_MEMORY_SEARCH = False       # Enable enhanced memory search

# === GAME INTEGRATION ===
PLAYING_GAME = False            # Legacy flag for game integration
PLAYING_MINECRAFT = True       # Enable Minecraft bot integration
IN_GROUP_CHAT = False           # Enable group chat conversation mode

# === PROMPT COMPONENTS ===
# Control what gets included in AI prompts
INCLUDE_SYSTEM_PROMPT = True          # Include system/personality prompt
INCLUDE_MEMORY_CONTEXT = True         # Include relevant memory context
INCLUDE_VISION_RESULTS = True         # Include vision analysis in prompt
INCLUDE_SEARCH_RESULTS = False         # Include web search results in prompt
INCLUDE_TOOL_METADATA = False         # Include execution metadata
INCLUDE_ENHANCED_MEMORY = False       # Include enhanced memory search
INCLUDE_CHAT_HISTORY = True           # Include recent conversation history

# === MINECRAFT SPECIFIC ===
INCLUDE_MINECRAFT_CONTEXT = True     # Include Minecraft environment data
SEND_MINECRAFT_MESSAGE = False        # Send responses to Minecraft chat
SEND_MINECRAFT_COMMAND = True        # Execute Minecraft commands from responses

# === MEMORY MANAGEMENT ===
SAVE_MEMORY = True                    # Save conversations to memory system
MEMORY_LENGTH = 6                     # Number of recent interactions to keep
PROMPT_TIMEOUT = 600                  # Timeout for prompt processing (seconds)

# === OUTPUT ACTIONS ===
AVATAR_ANIMATIONS = False             # Trigger avatar animations from responses
AVATAR_SPEECH = False                 # Enable text-to-speech output

# === DEBUGGING AND LOGGING ===
LOG_TOOL_EXECUTION = True            # Log when tools are executed
LOG_PROMPT_CONSTRUCTION = True       # Log prompt building process
LOG_RESPONSE_PROCESSING = True       # Log response generation steps
LOG_MINECRAFT_EXECUTION = True       # Log Minecraft-specific operations

# Note: Control methods (toggle_feature, set_feature, etc.) are available in:
# from BASE.core.control_methods import ControlManager