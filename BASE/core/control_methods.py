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

    def get_status_summary(self):
        """Get a human-readable summary of current settings using actual control values"""
        summary = []
        if not self.controls:
            summary.append("Controls module not available.")
            return "\n".join(summary)
            
        summary.append("=== AI CAPABILITIES ===")
        summary.append(f"Search: {'ON' if self.controls.USE_SEARCH else 'OFF'}")
        summary.append(f"Vision: {'ON' if self.controls.USE_VISION else 'OFF'}")
        summary.append(f"Memory Search: {'ON' if self.controls.USE_LONG_MEMORY else 'OFF'}")
        summary.append(f"Base Memory: {'ON' if self.controls.USE_BASE_MEMORY else 'OFF'}")
        summary.append(f"Short Memory: {'ON' if self.controls.USE_SHORT_MEMORY else 'OFF'}")
        summary.append(f"Long Memory: {'ON' if self.controls.USE_LONG_MEMORY else 'OFF'}")
        
        summary.append("\n=== PROMPT INCLUDES ===")
        summary.append(f"System Prompt: {'ON' if self.controls.INCLUDE_SYSTEM_PROMPT else 'OFF'}")
        summary.append(f"Vision Results: {'ON' if self.controls.INCLUDE_VISION_RESULTS else 'OFF'}")
        summary.append(f"Search Results: {'ON' if self.controls.INCLUDE_SEARCH_RESULTS else 'OFF'}")
        summary.append(f"Base Memory: {'ON' if self.controls.INCLUDE_BASE_MEMORY else 'OFF'}")
        summary.append(f"Short Memory: {'ON' if self.controls.INCLUDE_SHORT_MEMORY else 'OFF'}")
        summary.append(f"Long Memory: {'ON' if self.controls.INCLUDE_LONG_MEMORY else 'OFF'}")
        summary.append(f"Chat History: {'ON' if self.controls.INCLUDE_SHORT_MEMORY else 'OFF'}")
        
        summary.append("\n=== OUTPUT ===")
        summary.append(f"Animations: {'ON' if self.controls.AVATAR_ANIMATIONS else 'OFF'}")
        summary.append(f"Speech: {'ON' if self.controls.AVATAR_SPEECH else 'OFF'}")
        summary.append(f"Save Memory: {'ON' if self.controls.SAVE_MEMORY else 'OFF'}")

        summary.append("\n=== MODES ===")
        summary.append(f"Minecraft: {'ON' if self.controls.PLAYING_MINECRAFT else 'OFF'}")
        
        summary.append("\n=== DEBUGGING ===")
        summary.append(f"Prompt Logs: {'ON' if self.controls.LOG_PROMPT_CONSTRUCTION else 'OFF'}")
        summary.append(f"Response Logs: {'ON' if self.controls.LOG_RESPONSE_PROCESSING else 'OFF'}")
        summary.append(f"Minecraft Logs: {'ON' if self.controls.LOG_MINECRAFT_EXECUTION else 'OFF'}")
        
        return "\n".join(summary)

    def validate_minecraft_config(self):
        """Check if Minecraft configuration is valid using actual control values"""
        if not self.controls:
            print("Warning: Controls module not available.")
            return False
            
        if self.controls.PLAYING_MINECRAFT:
            # Check required dependencies for Minecraft mode
            if not self.controls.INCLUDE_SYSTEM_PROMPT:
                print("Warning: Minecraft mode enabled but system prompt disabled")
                
            if self.controls.SEND_MINECRAFT_COMMAND or self.controls.SEND_MINECRAFT_MESSAGE:
                if not self.controls.INCLUDE_MINECRAFT_CONTEXT:
                    print("Warning: Minecraft commands/messages enabled but context disabled")
                    return False
        return True

    def validate_memory_config(self):
        """Check if memory configuration is valid using actual control values"""
        if not self.controls:
            print("Warning: Controls module not available.")
            return False
            
        return True

    def validate_tool_config(self):
        """Check if tool configuration is valid using actual control values"""
        if not self.controls:
            print("Warning: Controls module not available.")
            return False
            
        if self.controls.USE_VISION and not self.controls.INCLUDE_VISION_RESULTS:
            print("Warning: Vision enabled but results not included in prompts")
            
        if self.controls.USE_SEARCH and not self.controls.INCLUDE_SEARCH_RESULTS:
            print("Warning: Search enabled but results not included in prompts")
            
        return True

    def validate_all_configs(self):
        """Validate all configurations using actual control values"""
        return (self.validate_minecraft_config() and 
                self.validate_memory_config() and 
                self.validate_tool_config())

    def get_control_dependencies(self):
        """Get a mapping of control dependencies"""
        return {
            'USE_VISION': ['INCLUDE_VISION_RESULTS'],
            'USE_SEARCH': ['INCLUDE_SEARCH_RESULTS'],
            'USE_LONG_MEMORY': ['INCLUDE_LONG_MEMORY'],
            'PLAYING_MINECRAFT': ['INCLUDE_SYSTEM_PROMPT', 'INCLUDE_MINECRAFT_CONTEXT'],
            'SEND_MINECRAFT_COMMAND': ['PLAYING_MINECRAFT', 'INCLUDE_MINECRAFT_CONTEXT'],
            'SEND_MINECRAFT_MESSAGE': ['PLAYING_MINECRAFT'],
            'INCLUDE_ENHANCED_MEMORY': ['USE_LONG_MEMORY'],
        }

    def auto_fix_dependencies(self):
        """Automatically fix control dependencies"""
        dependencies = self.get_control_dependencies()
        fixed = []
        
        for control, deps in dependencies.items():
            if hasattr(self.controls, control) and getattr(self.controls, control):
                for dep in deps:
                    if hasattr(self.controls, dep) and not getattr(self.controls, dep):
                        setattr(self.controls, dep, True)
                        fixed.append(f"Enabled {dep} (required by {control})")
        
        return fixed

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
        
        # Test dependency auto-fixing
        fixes = global_control_manager.auto_fix_dependencies()
        if fixes:
            print(f"\nAuto-fixed dependencies: {fixes}")
    else:
        print("Control manager not available for self-test")