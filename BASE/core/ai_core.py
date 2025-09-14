# Filename: core/ai_core.pytoggle_feature
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
from BASE.memory_methods.memory_manager import MemoryManager
from BASE.core.minecraft_integration import MinecraftIntegration
from BASE.core.config import Config
from BASE.core.control_methods import ControlManager

from personality.SYS_MSG import *
from personality.bot_info import *
from personality import controls

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
        
        # Create MinecraftIntegration instance without config dependencies
        self.minecraft_integration = MinecraftIntegration()
        
        if self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + "[AI Core] Initialized successfully" + resetTColor)
            print(systemTColor + f"[Controls] System: {self.controls.INCLUDE_SYSTEM_PROMPT}, Base Memory: {self.controls.INCLUDE_BASE_MEMORY}, Short Memory: {self.controls.INCLUDE_SHORT_MEMORY}, Long Memory: {self.controls.INCLUDE_LONG_MEMORY}, Vision: {self.controls.INCLUDE_VISION_RESULTS}, Search: {self.controls.INCLUDE_SEARCH_RESULTS}" + resetTColor)
            print(systemTColor + f"[Controls] Minecraft: {self.controls.PLAYING_MINECRAFT}, Avatar Animations: {self.controls.AVATAR_ANIMATIONS}" + resetTColor)
            
            # Show memory system status
            memory_stats = self.memory_manager.get_memory_stats()
            print(systemTColor + f"[Memory] Current day entries: {memory_stats['current_day_entries']}, Past day entries: {memory_stats['past_day_unsummarized_entries']}, Daily summaries: {memory_stats['daily_summary_embeddings_count']}, Base knowledge: {memory_stats['base_embeddings_count']}" + resetTColor)

    def set_warudo_manager(self, warudo_manager):
        """Set the Warudo manager for animations"""
        self.warudo_manager = warudo_manager
        print(systemTColor + f"[Debug] Warudo manager set: {self.warudo_manager is not None}" + resetTColor)
        if self.warudo_manager:
            print(systemTColor + f"[Debug] Warudo WebSocket URL: {self.warudo_manager.controller.websocket_url}" + resetTColor)
            print(systemTColor + f"[Debug] Warudo enabled: {self.warudo_manager.enabled}" + resetTColor)
            print(systemTColor + f"[Debug] Warudo connected: {self.warudo_manager.controller.ws_connected}" + resetTColor)

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

        tool_context = await self._execute_tools(user_text)

        system_prompt = None
        if self.controls.INCLUDE_SYSTEM_PROMPT:
            system_prompt = self._get_system_prompt()

        prompt_parts = []
        if tool_context.strip():
            prompt_parts.append(tool_context)

        if self.controls.INCLUDE_SHORT_MEMORY and self.history:
            recent_history = self.history
            history_section = "\n[RECENT_CHAT_HISTORY]\n"
            for entry in recent_history:
                role = entry['role'].upper()
                content = entry['content']
                history_section += f"{role}: {content}\n"
            prompt_parts.append(history_section)

        # Simplified Minecraft context handling
        if self.controls.PLAYING_MINECRAFT and self.controls.INCLUDE_MINECRAFT_CONTEXT:
            minecraft_context = await self.minecraft_integration.handle_vision(user_text, True)
            if minecraft_context:
                prompt_parts.append(minecraft_context)

        user_input_label = "[USER]"
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

        # Handle animations with comprehensive debugging
        print(systemTColor + f"[ANIMATION CHECK] Starting animation processing..." + resetTColor)
        print(f"[ANIMATION CHECK] controls.AVATAR_ANIMATIONS = {self.controls.AVATAR_ANIMATIONS}")
        print(f"[ANIMATION CHECK] self.warudo_manager exists = {self.warudo_manager is not None}")
        
        if self.controls.AVATAR_ANIMATIONS and self.warudo_manager:
            print(systemTColor + f"[ANIMATION] Conditions met, processing reply: '{reply[:50]}...'" + resetTColor)
            print(f"[ANIMATION] WebSocket connected: {self.warudo_manager.controller.ws_connected}")
            print(f"[ANIMATION] Warudo enabled: {self.warudo_manager.enabled}")
            
            try:
                print(systemTColor + "[ANIMATION] Calling detect_and_send_animations..." + resetTColor)
                self.warudo_manager.detect_and_send_animations(reply)
                print(systemTColor + "[ANIMATION] Animation detection completed successfully" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[ANIMATION ERROR] Animation failed: {e}" + resetTColor)
                import traceback
                traceback.print_exc()
        else:
            reasons = []
            if not self.controls.AVATAR_ANIMATIONS:
                reasons.append("AVATAR_ANIMATIONS is False")
            if not self.warudo_manager:
                reasons.append("warudo_manager is None")
            print(systemTColor + f"[ANIMATION] Skipped - Reasons: {', '.join(reasons)}" + resetTColor)

        # Minecraft command handling - use the integration properly
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

        # Minecraft chat handling 
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

        # Memory saving with day-based logic
        if self.controls.SAVE_MEMORY:
            context_to_save = user_text
            if self.controls.PLAYING_MINECRAFT and self.minecraft_integration:
                context_to_save = await self.minecraft_integration.enhance_memory_context(user_text, context_to_save)
            
            # Save interaction - this goes to memory.json as current day entries
            self.memory_manager.save_interaction(context_to_save, reply)
            self.interaction_count += 1
            
            # Check for auto-summarization of past days
            self._check_auto_summarize()

            # if self.controls.IN_GROUP_CHAT:
            #     self.history.extend([
            #         {"role": "user", "content": user_text},
            #         {"role": "assistant", "content": reply},
            #     ])
            #     if len(self.history) > (self.controls.MEMORY_LENGTH * 2):
            #         self.history = self.history[-(self.controls.MEMORY_LENGTH * 2):]

        return reply.strip()

    def _capture_screenshot(self) -> str:
        """Capture screenshot and return as base64"""
        if self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + "Taking desktop screenshot" + resetTColor)
        buf = BytesIO()
        pyautogui.screenshot().save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def _get_memory_context(self, query: str) -> str:
        """Get enhanced memory context based on control variables using day-based system"""
        include_base = self.config.include_base_memory
        
        # Use control variables to determine memory search behavior
        if self.controls.USE_LONG_MEMORY:
            # Force long-term memory search when USE_LONG_MEMORY is enabled
            # This will search both daily summaries and base knowledge
            memory_context = self.memory_manager.get_memory_context(query, include_base=include_base, force_long_term=True)
            
            # Enhanced memory search for additional base knowledge when enabled
            if self.controls.INCLUDE_ENHANCED_MEMORY and include_base:
                # Always do enhanced search when the control is enabled, regardless of query content
                base_results = self.memory_manager.search_base_memory_only(query, k=self.config.base_memory_search_results)
                if base_results:
                    memory_context += "\n=== ADDITIONAL BASE KNOWLEDGE ===\n"
                    for result in base_results:
                        source_file = result['metadata'].get('source_file', 'unknown')
                        memory_context += f"- {result['text']} [From: {source_file}] (similarity: {result['similarity']:.2f})\n"
        else:
            # When USE_LONG_MEMORY is disabled, only get current day context
            memory_context = self.memory_manager.get_short_term_context_only()
        
        return memory_context

    async def _execute_tools(self, user_text: str) -> str:
        tool_context_parts = []
        interaction_metadata = {
            "used_vision": False,
            "used_search": False,
            "used_memory": False,
            "used_minecraft": False,
            "memory_type": "current-day-only",
            "tool_context_length": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Simplified Minecraft tool execution
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

        # Vision tool - controlled by USE_VISION flag only
        if self.controls.USE_VISION and not self.controls.PLAYING_MINECRAFT:
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
        
        # Search tool - controlled by USE_SEARCH flag
        if self.controls.USE_SEARCH:
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
        
        # Memory context
        if self.controls.INCLUDE_SHORT_MEMORY or self.controls.INCLUDE_LONG_MEMORY:
            memory_context = self._get_memory_context(user_text)
            if memory_context.strip():
                tool_context_parts.append(f"\n[MEMORY_CONTEXT]\n{memory_context}")
                interaction_metadata["used_memory"] = True
                
                # Determine memory type based on control settings and content
                if self.controls.USE_LONG_MEMORY:
                    if "RELEVANT KNOWLEDGE" in memory_context:
                        if "Past Days' Summaries:" in memory_context and "Knowledge Base:" in memory_context:
                            interaction_metadata["memory_type"] = "daily-summaries+base-knowledge"
                        elif "Past Days' Summaries:" in memory_context:
                            interaction_metadata["memory_type"] = "daily-summaries"
                        elif "Knowledge Base:" in memory_context:
                            interaction_metadata["memory_type"] = "base-knowledge"
                    else:
                        interaction_metadata["memory_type"] = "current-day+long-term-search"
                else:
                    interaction_metadata["memory_type"] = "current-day-only"

        # if self.controls.INCLUDE_TOOL_METADATA:
        #     metadata_section = "\n[TOOL_EXECUTION_METADATA]\n"
        #     metadata_section += f"Vision: {'Used' if interaction_metadata['used_vision'] else 'Not used'}, "
        #     metadata_section += f"Search: {'Used' if interaction_metadata['used_search'] else 'Not used'}, "
        #     metadata_section += f"Memory: {interaction_metadata['memory_type']}, "
        #     metadata_section += f"Minecraft: {'Used' if interaction_metadata['used_minecraft'] else 'Not used'}\n"
        #     tool_context_parts.append(metadata_section)
        
        combined_tool_context = "".join(tool_context_parts)
        interaction_metadata["tool_context_length"] = len(combined_tool_context)
        
        return combined_tool_context

    def _check_auto_summarize(self):
        """Check and trigger automatic summarization of past day entries"""
        if (self.interaction_count - self.last_summarization) >= self.config.auto_summarize_threshold:
            if self.controls.LOG_TOOL_EXECUTION:
                print(systemTColor + f"[Memory] Auto-summarizing past days after {self.config.auto_summarize_threshold} interactions..." + resetTColor)
            
            # Check if there are any past day entries to summarize
            past_day_entries = self.memory_manager.get_past_day_entries_for_summarization()
            if len(past_day_entries) < 4:  # Need minimum entries for meaningful summary
                if self.controls.LOG_TOOL_EXECUTION:
                    print(systemTColor + f"[Memory] Only {len(past_day_entries)} past day entries - skipping auto-summarization" + resetTColor)
                return
            
            try:
                from BASE.memory_methods.summarizer import summarize_memory
                success = summarize_memory(self.memory_manager)
                if success:
                    self.last_summarization = self.interaction_count
                    if self.controls.LOG_TOOL_EXECUTION:
                        # Show updated memory stats after summarization
                        memory_stats = self.memory_manager.get_memory_stats()
                        print(systemTColor + f"[Memory] After summarization - Current day: {memory_stats['current_day_entries']}, Daily summaries: {memory_stats['daily_summary_embeddings_count']}" + resetTColor)
                else:
                    if self.controls.LOG_TOOL_EXECUTION:
                        print(systemTColor + "[Memory] Auto-summarization completed but no summaries were created" + resetTColor)
            except ImportError:
                print(errorTColor + "[Error] Summarizer module not found" + resetTColor)
            except Exception as e:
                print(errorTColor + f"[Error] Summarization failed: {e}" + resetTColor)

    def manual_summarize_past_days(self):
        """Manually trigger summarization of past day entries"""
        if self.controls.LOG_TOOL_EXECUTION:
            print(systemTColor + "[Memory] Manual summarization of past days requested..." + resetTColor)
        
        try:
            from BASE.memory_methods.summarizer import summarize_memory, get_days_available_for_summarization
            
            # Show what days are available for summarization
            available_days = get_days_available_for_summarization(self.memory_manager)
            if available_days:
                print(systemTColor + f"[Memory] Days available for summarization: {', '.join(available_days)}" + resetTColor)
                
                success = summarize_memory(self.memory_manager)
                if success:
                    print(systemTColor + "[Memory] Manual summarization completed successfully" + resetTColor)
                    # Show updated stats
                    memory_stats = self.memory_manager.get_memory_stats()
                    print(systemTColor + f"[Memory] Updated stats - Current day: {memory_stats['current_day_entries']}, Daily summaries: {memory_stats['daily_summary_embeddings_count']}" + resetTColor)
                    return True
                else:
                    print(systemTColor + "[Memory] Manual summarization completed but no summaries were created" + resetTColor)
                    return False
            else:
                print(systemTColor + "[Memory] No past day entries available for summarization" + resetTColor)
                return False
                
        except ImportError:
            print(errorTColor + "[Error] Summarizer module not found" + resetTColor)
            return False
        except Exception as e:
            print(errorTColor + f"[Error] Manual summarization failed: {e}" + resetTColor)
            return False

    def _get_system_prompt(self) -> str:
        if self.controls.PLAYING_MINECRAFT:
            return f"{minecraft_system_prompt}\n{minecraft_system_addendum}"
        else:
            return self.config.system_prompt

    def get_bot_info(self):
        memory_stats = self.memory_manager.get_memory_stats()
        bot_info = {
            'name': self.config.botname,
            'username': username,
            'current_day_entries': memory_stats['current_day_entries'],
            'past_day_unsummarized_entries': memory_stats['past_day_unsummarized_entries'],
            'total_memory_entries': memory_stats['total_memory_entries'],
            'daily_summary_embeddings_count': memory_stats['daily_summary_embeddings_count'],
            'base_embeddings_count': memory_stats['base_embeddings_count'],
            'interaction_count': self.interaction_count,
            'minecraft_ready': bool(self.minecraft_integration),
            'control_status': self.control_manager.get_all_features(),
            'current_settings': {
                'playing_minecraft': self.controls.PLAYING_MINECRAFT,
                # 'in_group_chat': self.controls.IN_GROUP_CHAT,
                'use_vision': self.controls.USE_VISION,
                'use_search': self.controls.USE_SEARCH,
                'avatar_animations': self.controls.AVATAR_ANIMATIONS
            }
        }
        
        # Get summarization candidate days
        try:
            candidate_days = self.memory_manager.get_summarization_candidate_days()
            bot_info['summarization_candidate_days'] = candidate_days
        except Exception as e:
            bot_info['summarization_candidate_days'] = []
        
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

    def get_memory_debug_info(self):
        """Get detailed memory system debug information"""
        try:
            memory_stats = self.memory_manager.get_memory_stats()
            current_day_entries = self.memory_manager.get_current_day_entries()
            past_day_entries = self.memory_manager.get_past_day_entries_for_summarization()
            candidate_days = self.memory_manager.get_summarization_candidate_days()
            
            debug_info = {
                'memory_stats': memory_stats,
                'current_day_entry_count': len(current_day_entries),
                'past_day_entry_count': len(past_day_entries),
                'summarization_candidate_days': candidate_days,
                'memory_file_exists': self.memory_manager.memory_file.exists(),
                'embeddings_file_exists': self.memory_manager.embeddings_file.exists(),
                'base_memory_dir_exists': self.memory_manager.base_memory_dir.exists(),
                'interaction_count': self.interaction_count,
                'last_summarization': self.last_summarization,
                'interactions_since_last_summary': self.interaction_count - self.last_summarization,
                'auto_summary_threshold': self.config.auto_summarize_threshold
            }
            
            return debug_info
        except Exception as e:
            return {'error': str(e)}

    def force_memory_cleanup(self):
        """Force cleanup of memory system - summarize all past day entries"""
        try:
            print(systemTColor + "[Memory] Forcing memory cleanup - summarizing all past day entries..." + resetTColor)
            
            from BASE.memory_methods.summarizer import summarize_memory
            success = summarize_memory(self.memory_manager)
            
            if success:
                self.last_summarization = self.interaction_count
                print(systemTColor + "[Memory] Forced memory cleanup completed successfully" + resetTColor)
                return True
            else:
                print(systemTColor + "[Memory] Forced memory cleanup completed but no summaries were created" + resetTColor)
                return False
                
        except Exception as e:
            print(errorTColor + f"[Error] Forced memory cleanup failed: {e}" + resetTColor)
            return False