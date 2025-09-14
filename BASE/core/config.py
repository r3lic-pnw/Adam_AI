# Filename: core/config.py
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Import bot info
from personality.bot_info import botname, username, textmodel, visionmodel, embedmodel

def load_config():
    """Load configuration from JSON file"""
    # Find project root (two levels up from this file: core -> botname_AI)
    project_root = Path(__file__).parent.parent
    config_path = project_root / "personality" / "config.json"
    
    with open(config_path, 'r') as f:
        return json.load(f)

@dataclass
class Config:
    def __init__(self):
        json_config = load_config()
        
        # Extract config sections
        ollama_config = json_config["ollama"]
        memory_config = json_config["memory"]
        warudo_config = json_config["warudo"]
        mindcraft_config = json_config["mindcraft"]
        features_config = json_config["features"]
        
        # Bot identity
        self.botname: str = botname
        self.username: str = username
        
        # Model configuration
        self.text_llm_model: str = os.getenv("TEXT_LLM_MODEL", textmodel)
        self.vision_llm_model: str = os.getenv("VISION_LLM_MODEL", visionmodel)
        self.embed_model: str = os.getenv("EMBED_MODEL", embedmodel)
        
        # System prompt
        from personality.SYS_MSG import system_prompt
        self.system_prompt: str = system_prompt
        
        # Ollama configuration
        self.ollama_endpoint: str = os.getenv("OLLAMA_ENDPOINT", ollama_config["endpoint"])
        self.ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", str(ollama_config["temperature"])))
        self.ollama_max_tokens: int = int(os.getenv("OLLAMA_MAX_TOKENS", str(ollama_config["max_tokens"])))
        self.ollama_top_p: float = float(os.getenv("OLLAMA_TOP_P", str(ollama_config["top_p"])))
        self.ollama_top_k: int = int(os.getenv("OLLAMA_TOP_K", str(ollama_config["top_k"])))
        self.ollama_repeat_penalty: float = float(os.getenv("OLLAMA_REPEAT_PENALTY", str(ollama_config["repeat_penalty"])))
        self.ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", str(ollama_config["timeout"])))
        self.ollama_seed: Optional[int] = ollama_config["seed"]
        
        # Override seed with environment variable if provided
        if os.getenv("OLLAMA_SEED"):
            seed_val = int(os.getenv("OLLAMA_SEED", "-1"))
            self.ollama_seed = seed_val if seed_val != -1 else None
        
        # Memory configuration
        self.max_context_entries: int = memory_config["max_context_entries"]
        self.embedding_search_results: int = memory_config["embedding_search_results"]
        self.base_memory_search_results: int = memory_config["base_memory_search_results"]
        self.auto_summarize_threshold: int = memory_config["auto_summarize_threshold"]
        self.include_base_memory: bool = memory_config["include_base_memory"]
        
        # Warudo configuration
        self.warudo_websocket_url: str = warudo_config["websocket_url"]
        self.warudo_enabled: bool = warudo_config["enabled"]
        self.warudo_auto_connect: bool = warudo_config["auto_connect"]
        self.warudo_connection_timeout: float = warudo_config["connection_timeout"]
        
        # Mindcraft configuration
        self.mindcraft_enabled: bool = mindcraft_config["enabled"]
        self.mindcraft_host: str = mindcraft_config["host"]
        self.mindcraft_port: int = mindcraft_config["port"]
        self.mindcraft_bot_name: str = mindcraft_config.get("bot_name", self.botname)
        self.mindcraft_debug: bool = mindcraft_config["debug"]
        
        # Feature toggles (can be overridden by individual interfaces)
        self.use_search: bool = features_config["use_search"]
        self.use_vision: bool = features_config["use_vision"]
        self.use_warudo: bool = features_config["use_warudo"]
        
        # Apply warudo feature toggle to warudo_enabled
        self.warudo_enabled = self.warudo_enabled and self.use_warudo