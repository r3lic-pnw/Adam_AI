# Filename: core/config.py
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Import bot info
try:
    from personality.bot_info import botname, username, textmodel, visionmodel, embedmodel
except ImportError:
    # Fallback values if import fails
    botname = "Anna"
    username = "User"
    textmodel = "gemma3:4b-it-q4_K_M"
    visionmodel = "gemma3:4b-it-q4_K_M"
    embedmodel = "nomic-embed-text"

def load_config():
    """Load configuration from JSON file with fallback to environment variables"""
    # Find project root (two levels up from this file: core -> botname_AI)
    project_root = Path(__file__).parent.parent
    config_path = project_root / "personality" / "config.json"
    
    # Default configuration
    default_config = {
        "ollama": {
            "endpoint": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "timeout": 600,
            "seed": None
        },
        "memory": {
            "max_context_entries": 50,
            "embedding_search_results": 3,
            "base_memory_search_results": 3,
            "auto_summarize_threshold": 100,
            "include_base_memory": True
        },
        "warudo": {
            "websocket_url": "ws://127.0.0.1:19190",
            "enabled": True,
            "auto_connect": True,
            "connection_timeout": 5.0
        },
        "mindcraft": {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 3001,
            "bot_name": None,
            "debug": True
        },
        "features": {
            "use_search": False,
            "use_vision": False,
            "use_warudo": True
        }
    }
    
    # Load from file if it exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Merge with defaults, allowing file to override
                for section, values in file_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse config.json due to JSON error: {e}")
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
    
    return default_config

@dataclass
class Config:
    def __init__(self):
        json_config = load_config()
        
        # Extract config sections
        ollama_config = json_config.get("ollama", {})
        memory_config = json_config.get("memory", {})
        warudo_config = json_config.get("warudo", {})
        mindcraft_config = json_config.get("mindcraft", {})
        features_config = json_config.get("features", {})
        
        # Bot identity
        self.botname: str = botname
        self.username: str = username
        
        # Model configuration
        self.text_llm_model: str = os.getenv("TEXT_LLM_MODEL", textmodel)
        self.vision_llm_model: str = os.getenv("VISION_LLM_MODEL", visionmodel)
        self.embed_model: str = os.getenv("EMBED_MODEL", embedmodel)
        
        # System prompt (imported separately)
        try:
            from personality.SYS_MSG import system_prompt
            self.system_prompt: str = system_prompt
        except ImportError:
            self.system_prompt: str = "You are a helpful AI assistant."
        
        # Ollama configuration
        self.ollama_endpoint: str = os.getenv("OLLAMA_ENDPOINT", ollama_config.get("endpoint", "http://localhost:11434"))
        self.ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", str(ollama_config.get("temperature", 0.7))))
        self.ollama_max_tokens: int = int(os.getenv("OLLAMA_MAX_TOKENS", str(ollama_config.get("max_tokens", 2048))))
        self.ollama_top_p: float = float(os.getenv("OLLAMA_TOP_P", str(ollama_config.get("top_p", 0.9))))
        self.ollama_top_k: int = int(os.getenv("OLLAMA_TOP_K", str(ollama_config.get("top_k", 40))))
        self.ollama_repeat_penalty: float = float(os.getenv("OLLAMA_REPEAT_PENALTY", str(ollama_config.get("repeat_penalty", 1.1))))
        self.ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", str(ollama_config.get("timeout", 600))))
        self.ollama_seed: Optional[int] = ollama_config.get("seed")
        
        # Override seed with environment variable if provided
        if os.getenv("OLLAMA_SEED"):
            seed_val = int(os.getenv("OLLAMA_SEED", "-1"))
            self.ollama_seed = seed_val if seed_val != -1 else None
        
        # Memory configuration
        self.max_context_entries: int = memory_config.get("max_context_entries", 6)
        self.embedding_search_results: int = memory_config.get("embedding_search_results", 3)
        self.base_memory_search_results: int = memory_config.get("base_memory_search_results", 3)
        self.auto_summarize_threshold: int = memory_config.get("auto_summarize_threshold", 100)
        self.include_base_memory: bool = memory_config.get("include_base_memory", True)
        
        # Warudo configuration
        self.warudo_websocket_url: str = warudo_config.get("websocket_url", "ws://127.0.0.1:19190")
        self.warudo_enabled: bool = warudo_config.get("enabled", True)
        self.warudo_auto_connect: bool = warudo_config.get("auto_connect", True)
        self.warudo_connection_timeout: float = warudo_config.get("connection_timeout", 5.0)
        
        # Mindcraft configuration
        self.mindcraft_enabled: bool = mindcraft_config.get("enabled", True)
        self.mindcraft_host: str = mindcraft_config.get("host", "127.0.0.1")
        self.mindcraft_port: int = mindcraft_config.get("port", 3001)
        self.mindcraft_bot_name: str = mindcraft_config.get("bot_name", self.botname)
        self.mindcraft_debug: bool = mindcraft_config.get("debug", True)
        
        # Feature toggles (can be overridden by individual interfaces)
        self.use_search: bool = features_config.get("use_search", False)
        self.use_vision: bool = features_config.get("use_vision", False)
        self.use_warudo: bool = features_config.get("use_warudo", True)
        
        # Apply warudo feature toggle to warudo_enabled
        self.warudo_enabled = self.warudo_enabled and self.use_warudo