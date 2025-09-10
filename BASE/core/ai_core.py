# Filename: core/ai_core.py
import os
import sys
import base64
import json
import time
import requests
import re
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import pyautogui
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from BASE.tools.query import web_search_summary
from BASE.memory_methods.memory_manipulation import MemoryManager
from BASE.core.minecraft_integration import MinecraftIntegration
from BASE.core.config import Config
from BASE.core.control_methods import ControlManager

from personality.SYS_MSG import *
from personality.bot_info import botname, username, textmodel, visionmodel, embedmodel, \
    systemTColor, toolTColor, errorTColor, resetTColor
from personality import controls

# Constants
VISION_KEYWORDS = ["screen", "image", "see", "look", "monitor", "display", "show", "screenshot"]
SEARCH_KEYWORDS = ["search", "find", "look up", "web", "internet", "google", "query", "browse"]
MEMORY_KEYWORDS = ["remember", "recall", "memory", "past", "history", "previous", "before", "earlier"]
MINECRAFT_KEYWORDS = ["go", "move", "collect", "gather", "mine", "build", "craft", "attack", "follow", "come"]

# Regex for thinking tags, pre-compiled for efficiency
THINK_PATTERN = re.compile(r'<think>(.*?)</think>', re.DOTALL)

class AICore:
    def __init__(self, config, controls_module):
        self.config = Config()
        self.controls = controls_module
        self.control_manager = ControlManager(controls_module)
        
        self.memory_manager = MemoryManager(
            project_root=project_root,
            ollama_endpoint=config.ollama_endpoint,
            embed_model=config.embed_model,
            botname=config.botname,
            username=username,
            max_context_entries=config.max_context_entries
        )
        
        # State tracking
        self.interaction_count = 0
        self.last_summarization = 0
        self.history: List[dict] = []
        
        # External integrations (set by interface)
        self.warudo_manager = None
        
        # FIXED: Create MinecraftIntegration instance without config dependencies
        self.minecraft_integration = MinecraftIntegration()
        
        if self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + "[AI Core] Initialized successfully" + resetTColor)
            print(systemTColor + f"[Controls] System: {self.controls.INCLUDE_SYSTEM_PROMPT}, Memory: {self.controls.INCLUDE_MEMORY_CONTEXT}, Vision: {self.controls.INCLUDE_VISION_RESULTS}, Search: {self.controls.INCLUDE_SEARCH_RESULTS}" + resetTColor)
            print(systemTColor + f"[Controls] Minecraft: {self.controls.PLAYING_MINECRAFT}, Group Chat: {self.controls.IN_GROUP_CHAT}" + resetTColor)

    def set_warudo_manager(self, warudo_manager):
        """Set the Warudo manager for animations"""
        self.warudo_manager = warudo_manager

    def set_minecraft_integration(self, minecraft_integration):
        """Set the Minecraft integration handler (deprecated - now created in __init__)"""
        if minecraft_integration:
            self.minecraft_integration = minecraft_integration
    
    def get_control_manager(self):
        """Get the control manager for external access"""
        return self.control_manager
    
    def update_control_setting(self, setting_name, value):
        """Update a control setting and log the change"""
        success = self.control_manager.set_feature(setting_name, value)
        if success and self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + f"[Controls] Updated {setting_name}: {value}" + resetTColor)
            
            # Auto-validate configuration after changes
            if not self.control_manager.validate_all_configs():
                print(systemTColor + "[Controls] Warning: Configuration validation failed after change" + resetTColor)
        return success
    
    def toggle_control_setting(self, setting_name):
        """Toggle a boolean control setting"""
        new_value = self.control_manager.toggle_feature(setting_name)
        if new_value is not None and self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + f"[Controls] Toggled {setting_name}: {new_value}" + resetTColor)
        return new_value
    
    def load_control_preset(self, preset_name):
        """Load a control preset configuration"""
        success = self.control_manager.load_preset(preset_name)
        if success and self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + f"[Controls] Loaded preset: {preset_name}" + resetTColor)
            print(systemTColor + self.control_manager.get_status_summary() + resetTColor)
        return success

    def _call_ollama(self, prompt: str, model: str, system_prompt: Optional[str] = None, image_data: str = "") -> str:
        """Call Ollama API with proper vision support and optimized parameters"""
        start_time = time.time()
        try:
            if image_data:
                url = f"{self.config.ollama_endpoint}/api/chat"
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt, "images": [image_data]})
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 512,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                }
            else:
                url = f"{self.config.ollama_endpoint}/api/generate"
                full_prompt = ""
                if system_prompt:
                    full_prompt += f"{system_prompt}\n\n"
                full_prompt += prompt
                payload = {
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 256,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_ctx": 2048,
                    "num_predict": 256,
                    "stop": ["Human:", "User:", "Assistant:", "\n\n"]
                }
            
            if self.config.ollama_seed is not None:
                payload["seed"] = self.config.ollama_seed
                    
            if self.controls.LOG_RESPONSE_PROCESSING:
                print(systemTColor + f"[Ollama] Calling {model} with {'vision' if image_data else 'text'} input" + resetTColor)
            
            response = requests.post(url, json=payload, timeout=self.controls.PROMPT_TIMEOUT)
            end_time = time.time()
            
            response_time = end_time - start_time
            if self.controls.LOG_RESPONSE_PROCESSING:
                print(systemTColor + f"[Ollama] Response time: {response_time:.2f}s" + resetTColor)
            
            if response_time > 15:
                print(errorTColor + f"[WARNING] Slow response detected: {response_time:.2f}s" + resetTColor)
            
            response.raise_for_status()
            result = response.json()

            # Extract content from response
            content = result.get("response", "") or result.get("message", {}).get("content", "") or \
                      result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse thinking tags
            thinking_content = ""
            actual_response = content.strip()
            think_match = THINK_PATTERN.search(actual_response)
            if think_match:
                thinking_content = think_match.group(1).strip()
                actual_response = THINK_PATTERN.sub('', actual_response).strip()
            
            if thinking_content and self.controls.LOG_RESPONSE_PROCESSING:
                print(toolTColor + "[Model Thinking Process]:" + resetTColor)
                print(toolTColor + thinking_content + resetTColor)
                print()
            
            # Clean up response - preserve natural language
            cleaned_response = actual_response.strip()
            
            if self.controls.LOG_RESPONSE_PROCESSING:
                print(toolTColor + "[Ollama Final Response Text]:" + resetTColor, toolTColor + cleaned_response[:200] + "..." + resetTColor)
            return cleaned_response
            
        except requests.exceptions.RequestException as e:
            print(errorTColor + f"[Error] Ollama API call failed (RequestException): {e}" + resetTColor)
            return ""
        except json.JSONDecodeError as e:
            print(errorTColor + f"[Error] Ollama API call failed (JSON Decode Error): {e}" + resetTColor)
            return ""
        except Exception as e:
            print(errorTColor + f"[Error] Ollama API call failed (General Error): {e}" + resetTColor)
            import traceback
            traceback.print_exc()
            return ""

    async def generate_response(self, user_text: str) -> Optional[str]:
        if not user_text.strip():
            if self.controls.PLAYING_MINECRAFT:
                user_text = "Describe your next action."
            else:
                return None

        # Validate current configuration before processing
        if not self.control_manager.validate_all_configs():
            print(systemTColor + "[Warning] Configuration validation failed, continuing anyway..." + resetTColor)

        tool_context, interaction_metadata = await self._execute_tools(user_text)

        system_prompt = None
        if self.controls.INCLUDE_SYSTEM_PROMPT:
            system_prompt = self._get_system_prompt()

        prompt_parts = []
        if tool_context.strip():
            prompt_parts.append(tool_context)

        if self.controls.INCLUDE_CHAT_HISTORY and self.controls.IN_GROUP_CHAT and self.history:
            recent_history = self.history[-self.controls.MEMORY_LENGTH:]
            history_section = "\n[RECENT_CHAT_HISTORY]\n"
            for entry in recent_history:
                role = entry['role'].upper()
                content = entry['content'][:200] + "..." if len(entry['content']) > 200 else entry['content']
                history_section += f"{role}: {content}\n"
            prompt_parts.append(history_section)

        # FIXED: Simplified Minecraft context handling using the integration
        if self.controls.PLAYING_MINECRAFT and self.controls.INCLUDE_MINECRAFT_CONTEXT:
            minecraft_context = await self.minecraft_integration.handle_vision(user_text, True)
            if minecraft_context:
                prompt_parts.append(minecraft_context)

        user_input_label = "[USER_INPUT]" if self.controls.IN_GROUP_CHAT else "[USER]"
        prompt_parts.append(f"{user_input_label}\n{user_text}")

        if self.controls.PLAYING_MINECRAFT and self.minecraft_integration:
            prompt_parts.append("\n[RESPONSE_GUIDANCE]\nProvide natural language response that may include actionable commands. Be conversational but specific about any actions you want to take.")

        user_prompt = "\n\n".join(filter(None, prompt_parts))
        
        if self.controls.LOG_PROMPT_CONSTRUCTION:
            print(f"[Prompting] System prompt length: {len(system_prompt or '')} characters")
            print(f"[Prompting] User prompt length: {len(user_prompt)} characters")
            print(systemTColor + f"[Prompting] Using {self.config.text_llm_model} for response generation" + resetTColor)

        if self.controls.LOG_PROMPT_CONSTRUCTION:
            print("=== SYSTEM PROMPT ===")
            print(system_prompt or "No system prompt")
            print("=== USER PROMPT ===")  
            print(user_prompt)
            print("=== END PROMPTS ===")

        reply = self._call_ollama(user_prompt, self.config.text_llm_model, system_prompt)

        if not reply:
            print(errorTColor + "[ERROR] Received empty response from model" + resetTColor)
            return None

        # Handle animations first
        if self.controls.AVATAR_ANIMATIONS and self.warudo_manager:
            self.warudo_manager.detect_and_send_animations(reply)

        # FIXED: Minecraft command handling - use the integration properly
        if self.controls.PLAYING_MINECRAFT and self.controls.SEND_MINECRAFT_COMMAND:
            if self.controls.LOG_MINECRAFT_EXECUTION:
                print(systemTColor + "[Minecraft] Sending AI response for command processing" + resetTColor)
            try:
                await self.minecraft_integration.handle_response(reply)
            except Exception as e:
                print(errorTColor + f"[Minecraft] Error sending command: {e}" + resetTColor)
                if self.controls.LOG_MINECRAFT_EXECUTION:
                    import traceback
                    traceback.print_exc()

        # FIXED: Minecraft chat handling - use the integration properly  
        if self.controls.PLAYING_MINECRAFT and self.controls.SEND_MINECRAFT_MESSAGE and not self.controls.SEND_MINECRAFT_COMMAND:
            try:
                await self.minecraft_integration.send_minecraft_chat(reply)
                if self.controls.LOG_MINECRAFT_EXECUTION:
                    print(systemTColor + "[Minecraft] Chat message sent successfully" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Minecraft] Error sending chat message: {e}" + resetTColor)
                if self.controls.LOG_MINECRAFT_EXECUTION:
                    import traceback
                    traceback.print_exc()

        # Memory saving (keep existing logic)
        if self.controls.SAVE_MEMORY:
            context_to_save = user_text
            if self.controls.PLAYING_MINECRAFT and self.minecraft_integration:
                context_to_save = await self.minecraft_integration.enhance_memory_context(user_text, context_to_save)
            
            self.memory_manager.save_interaction(context_to_save, reply)
            self.interaction_count += 1
            
            self._check_auto_summarize()

            if self.controls.IN_GROUP_CHAT:
                self.history.extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": reply},
                ])
                if len(self.history) > (self.controls.MEMORY_LENGTH * 2):
                    self.history = self.history[-(self.controls.MEMORY_LENGTH * 2):]

        return reply.strip()

    def _capture_screenshot(self) -> str:
        """Capture screenshot and return as base64"""
        if self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + "Taking desktop screenshot" + resetTColor)
        buf = BytesIO()
        pyautogui.screenshot().save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def _get_memory_context(self, query: str) -> str:
        """Get enhanced memory context based on query"""
        include_base = self.config.include_base_memory
        
        memory_context = self.memory_manager.get_memory_context(query, include_base=include_base)
        
        # Enhanced memory search for specific queries
        if any(keyword in query.lower() for keyword in MEMORY_KEYWORDS) and self.controls.INCLUDE_ENHANCED_MEMORY:
            if "RELEVANT KNOWLEDGE" not in memory_context:
                if include_base:
                    base_results = self.memory_manager.search_base_memory_only(query, k=self.config.base_memory_search_results)
                    if base_results:
                        memory_context += "\n=== ADDITIONAL BASE KNOWLEDGE ===\n"
                        for result in base_results:
                            source_file = result['metadata'].get('source_file', 'unknown')
                            memory_context += f"- {result['text']} [From: {source_file}] (relevance: {result['relevance_score']:.2f})\n"
        
        return memory_context

    async def _execute_tools(self, user_text: str) -> tuple[str, dict]:
        tool_context_parts = []
        interaction_metadata = {
            "used_vision": False,
            "used_search": False,
            "used_memory": False,
            "used_minecraft": False,
            "memory_type": "short-term",
            "tool_context_length": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        needs_vision = any(keyword in user_text.lower() for keyword in VISION_KEYWORDS)
        needs_search = any(keyword in user_text.lower() for keyword in SEARCH_KEYWORDS)
        needs_memory = any(keyword in user_text.lower() for keyword in MEMORY_KEYWORDS)
        
        auto_vision_terms = ['what do you see', 'screen', 'desktop', 'window', 'around me']
        auto_search_terms = ['latest', 'current', 'recent news', 'today', 'now']
        
        auto_needs_vision = any(term in user_text.lower() for term in auto_vision_terms) and not needs_vision
        auto_needs_search = any(term in user_text.lower() for term in auto_search_terms) and not needs_search

        # FIXED: Simplified Minecraft tool execution
        if self.controls.PLAYING_MINECRAFT:
            try:
                if self.controls.LOG_TOOL_EXECUTION:
                    print(systemTColor + "[Tool] Minecraft context requested - getting bot environmental data..." + resetTColor)
                
                minecraft_context = await self.minecraft_integration.handle_vision(user_text, True)
                if minecraft_context and minecraft_context.strip():
                    tool_context_parts.append(minecraft_context)
                    interaction_metadata["used_minecraft"] = True
                    interaction_metadata["used_vision"] = True
                    
                    if self.controls.LOG_TOOL_EXECUTION:
                        print(toolTColor + f"[Minecraft] Context obtained: {len(minecraft_context)} characters" + resetTColor)
                        
            except Exception as e:
                print(errorTColor + f"[Minecraft] Error getting context: {e}" + resetTColor)

        if self.controls.USE_VISION and (needs_vision or auto_needs_vision) and not self.controls.PLAYING_MINECRAFT:
            try:
                if self.controls.LOG_TOOL_EXECUTION:
                    print(systemTColor + "[Tool] Vision analysis requested - capturing screenshot..." + resetTColor)
                screenshot_data = self._capture_screenshot()
                vision_analysis = self._call_ollama(
                    vision_model_prompt,
                    self.config.vision_llm_model,
                    vision_model_prompt,
                    screenshot_data
                )
                if vision_analysis and self.controls.INCLUDE_VISION_RESULTS:
                    tool_context_parts.append(f"\n[VISION ANALYSIS]: {vision_analysis}")
                    interaction_metadata["used_vision"] = True
                    if self.controls.LOG_TOOL_EXECUTION:
                        print(toolTColor + f"[Vision] Analysis complete: {len(vision_analysis)} characters" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Vision] Error: {e}" + resetTColor)
        
        if (needs_search or auto_needs_search) and self.controls.USE_SEARCH:
            try:
                if self.controls.LOG_TOOL_EXECUTION:
                    print(systemTColor + "[Tool] Web search requested..." + resetTColor)
                search_results = web_search_summary(user_text)
                if search_results and search_results != "[]" and self.controls.INCLUDE_SEARCH_RESULTS:
                    tool_context_parts.append(f"\n[SEARCH RESULTS]: {search_results}")
                    interaction_metadata["used_search"] = True
                    if self.controls.LOG_TOOL_EXECUTION:
                        print(toolTColor + f"[Search] Results obtained: {len(search_results)} characters" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Search] Error: {e}" + resetTColor)
        
        if self.controls.INCLUDE_MEMORY_CONTEXT:
            memory_context = self._get_memory_context(user_text)
            if memory_context.strip():
                tool_context_parts.append(f"\n[MEMORY_CONTEXT]\n{memory_context}")
                interaction_metadata["used_memory"] = True
                
                if "RELEVANT KNOWLEDGE" in memory_context or "ADDITIONAL BASE KNOWLEDGE" in memory_context:
                    interaction_metadata["memory_type"] = "long-term"

        if self.controls.INCLUDE_TOOL_METADATA:
            metadata_section = "\n[TOOL_EXECUTION_METADATA]\n"
            metadata_section += f"Vision: {'Used' if interaction_metadata['used_vision'] else 'Not used'}, "
            metadata_section += f"Search: {'Used' if interaction_metadata['used_search'] else 'Not used'}, "
            metadata_section += f"Memory: {interaction_metadata['memory_type']}, "
            metadata_section += f"Minecraft: {'Used' if interaction_metadata['used_minecraft'] else 'Not used'}\n"
            tool_context_parts.append(metadata_section)
        
        combined_tool_context = "".join(tool_context_parts)
        interaction_metadata["tool_context_length"] = len(combined_tool_context)
        
        return combined_tool_context, interaction_metadata

    def _check_auto_summarize(self):
        if (self.interaction_count - self.last_summarization) >= self.config.auto_summarize_threshold:
            if self.controls.LOG_TOOL_EXECUTION:
                print(systemTColor + f"[Memory] Auto-summarizing after {self.config.auto_summarize_threshold} interactions..." + resetTColor)
            
            try:
                from BASE.memory_methods.summarizer import summarize_memory
                summarize_memory(self.memory_manager)
                self.last_summarization = self.interaction_count
            except ImportError:
                print(errorTColor + "[Error] Summarizer module not found" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Error] Summarization failed: {e}" + resetTColor)

    def _get_system_prompt(self) -> str:
        if self.controls.IN_GROUP_CHAT:
            return f"{self.config.system_prompt}"
        elif self.controls.PLAYING_MINECRAFT:
            return f"{minecraft_system_prompt}\n{minecraft_system_addendum}"
        else:
            return self.config.system_prompt

    def get_bot_info(self):
        memory_stats = self.memory_manager.get_memory_stats()
        bot_info = {
            'name': self.config.botname,
            'username': username,
            'memory_entries': memory_stats['memory_entries'],
            'summary_embeddings_count': memory_stats['summary_embeddings_count'],
            'base_embeddings_count': memory_stats['base_embeddings_count'],
            'interaction_count': self.interaction_count,
            'minecraft_ready': bool(self.minecraft_integration),
            'control_status': self.control_manager.get_all_features(),
            'current_settings': {
                'playing_minecraft': self.controls.PLAYING_MINECRAFT,
                'in_group_chat': self.controls.IN_GROUP_CHAT,
                'use_vision': self.controls.USE_VISION,
                'use_search': self.controls.USE_SEARCH,
                'avatar_animations': self.controls.AVATAR_ANIMATIONS
            }
        }
        
        if self.minecraft_integration:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                minecraft_status = loop.run_until_complete(self.minecraft_integration.check_bot_status())
                bot_info['minecraft_status'] = minecraft_status
            except Exception as e:
                bot_info['minecraft_status'] = {'error': str(e)}
        
        return bot_info