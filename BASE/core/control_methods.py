# Filename: BASE/core/control_methods.py
"""
Control methods for dynamically managing AI functionality.
This module provides functions to modify control variables at runtime.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from personality import controls
except ImportError as e:
    print(f"Error importing controls module: {e}")
    controls = None

class ControlManager:
    """Manages dynamic control of AI features"""
    
    def __init__(self, controls_module=None):
        self.controls = controls_module or controls
        if not self.controls:
            raise ImportError("Controls module not available")
    
    def toggle_feature(self, feature_name):
        """Toggle a boolean feature on/off"""
        if hasattr(self.controls, feature_name):
            current_value = getattr(self.controls, feature_name)
            if isinstance(current_value, bool):
                new_value = not current_value
                setattr(self.controls, feature_name, new_value)
                return new_value
        return None

    def set_feature(self, feature_name, value):
        """Set a feature to a specific value"""
        if hasattr(self.controls, feature_name):
            setattr(self.controls, feature_name, value)
            return True
        return False

    def get_feature(self, feature_name):
        """Get current value of a feature"""
        return getattr(self.controls, feature_name, None)

    def get_all_features(self):
        """Return dictionary of all control variables and their values"""
        features = {}
        for name in dir(self.controls):
            if name.isupper() and not name.startswith('_'):
                value = getattr(self.controls, name)
                if isinstance(value, (bool, int, str)):
                    features[name] = value
        return features

    def reset_to_defaults(self):
        """Reset all features to their default safe values"""
        defaults = {
            # Core capabilities - conservative defaults
            'USE_SEARCH': False,
            'USE_VISION': False,
            'USE_MEMORY_SEARCH': False,
            
            # Game integration - off by default
            'PLAYING_GAME': False,
            'PLAYING_MINECRAFT': False,
            'IN_GROUP_CHAT': False,
            
            # Prompt components - sensible defaults
            'INCLUDE_SYSTEM_PROMPT': True,
            'INCLUDE_MEMORY_CONTEXT': True,
            'INCLUDE_VISION_RESULTS': True,
            'INCLUDE_SEARCH_RESULTS': True,
            'INCLUDE_TOOL_METADATA': False,
            'INCLUDE_ENHANCED_MEMORY': False,
            'INCLUDE_CHAT_HISTORY': True,
            
            # Minecraft - off by default
            'INCLUDE_MINECRAFT_CONTEXT': False,
            'SEND_MINECRAFT_MESSAGE': False,
            'SEND_MINECRAFT_COMMAND': False,
            
            # Memory - on by default
            'SAVE_MEMORY': True,
            'MEMORY_LENGTH': 6,
            'PROMPT_TIMEOUT': 600,
            
            # Output actions - off by default for safety
            'AVATAR_ANIMATIONS': False,
            'AVATAR_SPEECH': False,
            
            # Logging - off by default for performance
            'LOG_TOOL_EXECUTION': False,
            'LOG_PROMPT_CONSTRUCTION': False,
            'LOG_RESPONSE_PROCESSING': False,
            'LOG_MINECRAFT_EXECUTION': False,
        }
        
        for feature, value in defaults.items():
            if hasattr(self.controls, feature):
                setattr(self.controls, feature, value)

    def load_preset(self, preset_name):
        """Load a preset configuration"""
        presets = {
            'minimal': {
                'USE_SEARCH': False,
                'USE_VISION': False,
                'USE_MEMORY_SEARCH': False,
                'SAVE_MEMORY': False,
                'INCLUDE_MEMORY_CONTEXT': False,
                'AVATAR_ANIMATIONS': False,
                'AVATAR_SPEECH': False,
                'LOG_TOOL_EXECUTION': False,
            },
            'standard': {
                'USE_SEARCH': True,
                'USE_VISION': True,
                'USE_MEMORY_SEARCH': True,
                'SAVE_MEMORY': True,
                'INCLUDE_MEMORY_CONTEXT': True,
                'AVATAR_ANIMATIONS': False,
                'AVATAR_SPEECH': False,
                'LOG_TOOL_EXECUTION': False,
            },
            'full_features': {
                'USE_SEARCH': True,
                'USE_VISION': True,
                'USE_MEMORY_SEARCH': True,
                'SAVE_MEMORY': True,
                'INCLUDE_MEMORY_CONTEXT': True,
                'INCLUDE_ENHANCED_MEMORY': True,
                'AVATAR_ANIMATIONS': True,
                'AVATAR_SPEECH': True,
                'LOG_TOOL_EXECUTION': True,
            },
            'minecraft': {
                'PLAYING_MINECRAFT': True,
                'USE_VISION': True,
                'INCLUDE_MINECRAFT_CONTEXT': True,
                'SEND_MINECRAFT_MESSAGE': True,
                'SAVE_MEMORY': True,
                'LOG_MINECRAFT_EXECUTION': True,
            },
            'group_chat': {
                'IN_GROUP_CHAT': True,
                'INCLUDE_CHAT_HISTORY': True,
                'USE_SEARCH': True,
                'SAVE_MEMORY': True,
                'AVATAR_ANIMATIONS': False,
            },
            'debug': {
                'LOG_TOOL_EXECUTION': True,
                'LOG_PROMPT_CONSTRUCTION': True,
                'LOG_RESPONSE_PROCESSING': True,
                'LOG_MINECRAFT_EXECUTION': True,
                'INCLUDE_TOOL_METADATA': True,
            }
        }
        
        if preset_name in presets:
            for feature, value in presets[preset_name].items():
                if hasattr(self.controls, feature):
                    setattr(self.controls, feature, value)
            return True
        return False

    def get_status_summary(self):
        """Get a human-readable summary of current settings"""
        summary = []
        if not self.controls:
            summary.append("Controls module not available.")
            return "\n".join(summary)
        summary.append("=== AI CAPABILITIES ===")
        summary.append(f"Search: {'ON' if getattr(self.controls, 'USE_SEARCH', False) else 'OFF'}")
        summary.append(f"Vision: {'ON' if getattr(self.controls, 'USE_VISION', False) else 'OFF'}")
        summary.append(f"Memory Search: {'ON' if getattr(self.controls, 'USE_MEMORY_SEARCH', False) else 'OFF'}")
        
        summary.append("\n=== MODES ===")
        summary.append(f"Minecraft: {'ON' if getattr(self.controls, 'PLAYING_MINECRAFT', False) else 'OFF'}")
        summary.append(f"Group Chat: {'ON' if getattr(self.controls, 'IN_GROUP_CHAT', False) else 'OFF'}")
        
        summary.append("\n=== OUTPUT ===")
        summary.append(f"Animations: {'ON' if getattr(self.controls, 'AVATAR_ANIMATIONS', False) else 'OFF'}")
        summary.append(f"Speech: {'ON' if getattr(self.controls, 'AVATAR_SPEECH', False) else 'OFF'}")
        summary.append(f"Save Memory: {'ON' if getattr(self.controls, 'SAVE_MEMORY', False) else 'OFF'}")
        
        summary.append("\n=== DEBUGGING ===")
        summary.append(f"Tool Logs: {'ON' if getattr(self.controls, 'LOG_TOOL_EXECUTION', False) else 'OFF'}")
        summary.append(f"Prompt Logs: {'ON' if getattr(self.controls, 'LOG_PROMPT_CONSTRUCTION', False) else 'OFF'}")
        summary.append(f"Response Logs: {'ON' if getattr(self.controls, 'LOG_RESPONSE_PROCESSING', False) else 'OFF'}")
        
        return "\n".join(summary)

    def get_available_presets(self):
        """Get list of available presets"""
        return ['minimal', 'standard', 'full_features', 'minecraft', 'group_chat', 'debug']

    def validate_minecraft_config(self):
        """Check if Minecraft configuration is valid"""
        if not self.controls:
            print("Warning: Controls module not available.")
            return False
        if getattr(self.controls, 'PLAYING_MINECRAFT', False):
            required_features = ['INCLUDE_MINECRAFT_CONTEXT']
            missing = [f for f in required_features if not getattr(self.controls, f, False)]
            if missing:
                print(f"Warning: Minecraft mode enabled but missing: {missing}")
                return False
        return True

    def validate_memory_config(self):
        """Check if memory configuration is valid"""
        if not self.controls:
            print("Warning: Controls module not available.")
            return False
        if getattr(self.controls, 'SAVE_MEMORY', False) and not getattr(self.controls, 'INCLUDE_MEMORY_CONTEXT', False):
            print("Warning: Saving memory but not including memory context in prompts")
            return False
        return True

    def validate_all_configs(self):
        """Validate all configurations"""
        return self.validate_minecraft_config() and self.validate_memory_config()

    def auto_configure_for_mode(self, mode):
        """Automatically configure settings for a specific mode"""
        mode_configs = {
            'basic_chat': {
                'USE_SEARCH': False,
                'USE_VISION': False,
                'SAVE_MEMORY': True,
                'INCLUDE_MEMORY_CONTEXT': True,
                'AVATAR_SPEECH': False,
            },
            'enhanced_chat': {
                'USE_SEARCH': True,
                'USE_VISION': True,
                'SAVE_MEMORY': True,
                'INCLUDE_MEMORY_CONTEXT': True,
                'AVATAR_SPEECH': True,
            },
            'minecraft_mode': {
                'PLAYING_MINECRAFT': True,
                'USE_VISION': True,
                'INCLUDE_MINECRAFT_CONTEXT': True,
                'SEND_MINECRAFT_MESSAGE': True,
                'SAVE_MEMORY': True,
            },
            'presentation_mode': {
                'AVATAR_ANIMATIONS': True,
                'AVATAR_SPEECH': True,
                'USE_VISION': True,
                'LOG_TOOL_EXECUTION': False,
            }
        }
        
        if mode in mode_configs:
            for feature, value in mode_configs[mode].items():
                if hasattr(self.controls, feature):
                    setattr(self.controls, feature, value)
            return True
        return False

# Convenience functions for backward compatibility
def toggle_feature(feature_name):
    """Global function to toggle a feature"""
    manager = ControlManager()
    return manager.toggle_feature(feature_name)

def set_feature(feature_name, value):
    """Global function to set a feature"""
    manager = ControlManager()
    return manager.set_feature(feature_name, value)

def get_feature(feature_name):
    """Global function to get a feature value"""
    manager = ControlManager()
    return manager.get_feature(feature_name)

def get_status_summary():
    """Global function to get status summary"""
    manager = ControlManager()
    return manager.get_status_summary()

def load_preset(preset_name):
    """Global function to load a preset"""
    manager = ControlManager()
    return manager.load_preset(preset_name)

# Create a global instance for convenience
try:
    global_control_manager = ControlManager()
except ImportError:
    global_control_manager = None
    print("Warning: Could not initialize global control manager")

if __name__ == "__main__":
    # Self-test when run directly
    if global_control_manager:
        print("Control methods module self-test:")
        print(global_control_manager.get_status_summary())
        print("\nValidation:", "PASSED" if global_control_manager.validate_all_configs() else "FAILED")
        print(f"\nAvailable presets: {', '.join(global_control_manager.get_available_presets())}")
    else:
        print("Control manager not available for self-test")