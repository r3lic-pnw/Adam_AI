# Filename: core/minecraft_integration.py
import json
import time
import asyncio
import requests
from typing import Optional, Dict, Any, List
import re

from personality.SYS_MSG import minecraft_system_addendum, minecraft_system_prompt
from personality.bot_info import systemTColor, toolTColor, errorTColor, resetTColor
from personality.controls import *


class MinecraftIntegration:
    """Enhanced Minecraft-specific functionality and integration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Fixed URL - remove variable dependencies
        self.base_url = "http://127.0.0.1:3001"
        
        self.last_minecraft_vision = ""
        self.vision_cache_timeout = 30  # seconds
        self.last_vision_time = 0
        self.bot_status = {}
        self.last_status_check = 0
        self.status_cache_timeout = 10  # seconds
        self.last_action_time = 0
        self.action_cooldown = 2  # seconds between actions
        
        # Enhanced action patterns with better natural language understanding
        self.action_patterns = self._initialize_action_patterns()
        
        if LOG_MINECRAFT_EXECUTION:
            print(systemTColor + "[Minecraft Integration] Initialized successfully" + resetTColor)
            print(systemTColor + f"[Minecraft] Base URL: {self.base_url}" + resetTColor)
            print(systemTColor + f"[Minecraft] Loaded {len(self.action_patterns)} action patterns" + resetTColor)

    def _initialize_action_patterns(self) -> List[tuple]:
        """Initialize comprehensive action patterns for natural language parsing"""
        return [
            # Movement patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:go(?:ing)?|move|travel|walk|run|head)\s+(?:to\s+)?(?:coordinates?\s*)?(-?\d+)[\s,]+(-?\d+)(?:[\s,]+(-?\d+))?', 
             lambda m: f"go to {m.group(1)} {m.group(2)} {m.group(3) if m.group(3) else '~'}"),
            
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:follow|come (?:to|with)|stay (?:close to|near)|approach)\s+(?:the\s+)?(?:you|player)', 
             lambda m: "follow player"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:come (?:here|over)|approach|get closer)', 
             lambda m: "go near player"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:stop|halt|wait|stay put|stand still)', 
             lambda m: "stop"),

            # Resource gathering patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:collect|gather|get|find|mine|chop|cut)\s+(?:some\s+)?wood(?:\s+(?:logs?|planks?))?', 
             lambda m: "gather wood"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:collect|gather|get|find|mine|dig)\s+(?:some\s+)?stone(?:\s+blocks?)?', 
             lambda m: "gather stone"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:collect|gather|get|find|dig)\s+(?:some\s+)?dirt(?:\s+blocks?)?', 
             lambda m: "gather dirt"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:collect|gather|get|find|mine)\s+(?:some\s+)?(?:coal|iron|gold|diamond)(?:\s+ore)?', 
             lambda m: "gather ore"),

            # Building and crafting patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:craft|make|create)\s+(?:some\s+)?(?:wooden\s+)?planks?', 
             lambda m: "craft planks"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:craft|make|create)\s+(?:a\s+)?(?:wooden\s+)?(?:pickaxe|axe|shovel|sword|hoe)', 
             lambda m: "craft tools"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:place|put (?:down)?|build|set)\s+(?:a\s+|some\s+)?blocks?(?:\s+(?:here|there|down))?', 
             lambda m: "place block"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:break|destroy|remove|mine)\s+(?:this|that|the)?\s*block', 
             lambda m: "break block"),

            # Combat patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:attack|fight|kill|defend against)\s+(?:the\s+)?(?:hostile|enemy|monster|mob|zombie|skeleton|spider|creeper)', 
             lambda m: "attack hostile"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:defend|protect)\s+(?:myself|us)', 
             lambda m: "defend"),

            # Inventory patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:drop|throw|discard)\s+(?:this|that|my)?\s*(?:item|block|tool)', 
             lambda m: "drop item"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:equip|hold|use|switch to)\s+(?:my\s+)?(?:pickaxe|axe|sword|shovel|tool)', 
             lambda m: "equip tool"),

            # Exploration patterns
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:explore|look around|search|investigate)\s+(?:the\s+)?(?:area|surroundings)?', 
             lambda m: "look around"),
             
            (r'(?:i(?:\'ll|\'m| will| am going to)?\s+)?(?:find|locate|search for)\s+(?:a\s+)?(?:cave|village|structure|chest)', 
             lambda m: "explore area"),

            # Communication acknowledgments (no action needed)
            (r'(?:i see|i understand|got it|okay|alright)', 
             lambda m: None),
        ]

    def get_system_prompt(self) -> str:
        """Get the Minecraft-specific system prompt"""
        return f"""{minecraft_system_prompt}
        {minecraft_system_addendum}
        """

    async def check_bot_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Check if the Minecraft bot is ready and get its status"""
        current_time = time.time()
        
        if not force_refresh and (current_time - self.last_status_check) < self.status_cache_timeout and self.bot_status:
            return self.bot_status
        
        try:
            response = await self._make_request('GET', '/api/status')
            if response and response.get('connected') and response.get('spawned'):
                self.bot_status = response
                self.last_status_check = current_time
                return response
            else:
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + f"[Minecraft Status] Bot not ready: {response}" + resetTColor)
                return response or {}
                
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Status] Error checking bot status: {e}" + resetTColor)
            return {}

    async def handle_vision(self, user_text: str, should_capture_vision: bool) -> str:
        """Handle vision requests in Minecraft mode with improved caching"""
        if LOG_MINECRAFT_EXECUTION:
            print(systemTColor + "[Minecraft] Getting bot's environmental data..." + resetTColor)
        
        # Check if bot is ready first
        status = await self.check_bot_status()
        if not status.get('connected') or not status.get('spawned'):
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Vision] Bot not ready - connected: {status.get('connected')}, spawned: {status.get('spawned')}" + resetTColor)
            return ""
        
        # Check cache first
        current_time = time.time()
        if (current_time - self.last_vision_time) < self.vision_cache_timeout and self.last_minecraft_vision:
            if LOG_MINECRAFT_EXECUTION:
                print(toolTColor + "[Minecraft Vision] Using cached environmental data" + resetTColor)
        else:
            # Get fresh vision data
            vision_analysis = await self._capture_minecraft_vision()
            
            if vision_analysis and not vision_analysis.startswith("Bot environmental data unavailable"):
                # Store full data but truncate for context if needed
                self.last_minecraft_vision = vision_analysis
                self.last_vision_time = current_time
                
                if LOG_MINECRAFT_EXECUTION:
                    print(toolTColor + f"[Minecraft Vision] Fresh environmental data received: {len(vision_analysis)} characters" + resetTColor)
            else:
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + f"[Minecraft Vision] Failed to get environmental data: {vision_analysis}" + resetTColor)
                return ""
        
        if INCLUDE_MINECRAFT_CONTEXT and self.last_minecraft_vision:
            # Truncate context if too long to prevent token overflow
            context = self.last_minecraft_vision
            if len(context) > 800:
                context = context[:750] + "... [data truncated for context]"
            return f"\n[MINECRAFT_BOT_PERSPECTIVE]: {context}"
        
        return ""

    async def _capture_minecraft_vision(self) -> str:
        """Get Minecraft bot's environmental vision data via API"""
        if LOG_MINECRAFT_EXECUTION:
            print(systemTColor + "Getting Minecraft bot's environmental data..." + resetTColor)
        
        try:
            response = await self._make_request('GET', '/api/vision')
            
            if response and response.get('status') == 'success' and 'vision' in response:
                vision_data = response['vision']
                description = self._format_vision_data(vision_data)
                
                if LOG_MINECRAFT_EXECUTION:
                    print(toolTColor + "[Minecraft Vision] Successfully received and formatted environmental data" + resetTColor)
                return description
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response'
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + f"[Minecraft Vision] API error: {error_msg}" + resetTColor)
                return f"Bot environmental data unavailable - {error_msg}"
                
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Vision] Error requesting vision: {e}" + resetTColor)
            return f"Bot environmental data unavailable - {str(e)}"

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: int = 15) -> Optional[Dict]:
        """Make HTTP request to the Minecraft bot API with better error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            loop = asyncio.get_event_loop()
            
            if method.upper() == 'GET':
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.get(url, timeout=timeout)
                )
            elif method.upper() == 'POST':
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(url, json=data, timeout=timeout)
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + f"[Minecraft API] HTTP {response.status_code}: {response.text[:100]}..." + resetTColor)
                return {"status": "error", "error": f"HTTP {response.status_code}", "details": response.text[:200]}
                
        except requests.exceptions.ConnectionError:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft API] Could not connect to {url}" + resetTColor)
            return {"status": "error", "error": "Connection refused"}
        except requests.exceptions.Timeout:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft API] Request timeout for {url}" + resetTColor)
            return {"status": "error", "error": "Request timeout"}
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft API] Request error: {e}" + resetTColor)
            return {"status": "error", "error": str(e)}

    def _format_vision_data(self, vision: dict) -> str:
        """Format vision data into concise descriptive text for the AI"""
        if not vision:
            return "No environmental data available"
        
        description_parts = []
        
        # Essential information first
        pos = vision.get('position', {})
        health = vision.get('health', 0)
        food = vision.get('food', 0)
        
        description_parts.append(f"Position: ({pos.get('x', '?'):.1f}, {pos.get('y', '?'):.1f}, {pos.get('z', '?'):.1f}). Health: {health}/20, Food: {food}/20.")
        
        # Time and weather
        time_info = vision.get('time', {})
        weather_info = vision.get('weather', {})
        phase = time_info.get('phase', 'unknown')
        day = time_info.get('day', 0)
        weather_desc = f"Day {day}, {phase}"
        if weather_info.get('isRaining'):
            weather_desc += " (raining)"
        description_parts.append(f"Time: {weather_desc}.")
        
        # What I'm looking at (most important for interaction)
        target = vision.get('targetBlock')
        if target:
            target_pos = target.get('position', {})
            description_parts.append(f"Looking at: {target.get('name', 'unknown')} at ({target_pos.get('x')}, {target_pos.get('y')}, {target_pos.get('z')}).")
        
        # Inventory status
        inventory = vision.get('inventory', {})
        item_in_hand = inventory.get('itemInHand')
        if item_in_hand and item_in_hand.get('name'):
            hand_desc = f"Holding: {item_in_hand['name']}"
            if item_in_hand.get('count', 1) > 1:
                hand_desc += f" x{item_in_hand['count']}"
            description_parts.append(hand_desc + ".")
        else:
            description_parts.append("Empty hands.")
        
        total_items = inventory.get('totalItems', 0)
        description_parts.append(f"Inventory: {total_items} items.")
        
        # Immediate surroundings
        surroundings = vision.get('surroundings', {})
        if surroundings:
            ground = surroundings.get('ground', 'air')
            if ground != 'air':
                description_parts.append(f"Standing on: {ground}.")
        
        # Nearby entities (prioritize threats and players)
        entities = vision.get('entitiesInSight', [])
        if entities:
            players = [e for e in entities if e.get('isPlayer')]
            hostiles = [e for e in entities if e.get('isHostile') and not e.get('isPlayer')]
            
            if players:
                player_names = [p.get('name', 'unknown') for p in players[:2]]
                description_parts.append(f"Players nearby: {', '.join(player_names)}.")
            
            if hostiles:
                hostile_types = [f"{h.get('type', 'unknown')} ({h.get('distance', '?'):.1f}m)" for h in hostiles[:3]]
                description_parts.append(f"Hostile entities: {', '.join(hostile_types)}.")
        
        # Visible blocks (only interesting ones)
        blocks = vision.get('blocksInSight', [])
        if blocks:
            interesting_blocks = []
            for block in blocks[:4]:
                name = block.get('name', '')
                if name and name not in ['air', 'grass_block', 'dirt', 'stone']:
                    distance = block.get('distance', 0)
                    interesting_blocks.append(f"{name} ({distance:.1f}m)")
            
            if interesting_blocks:
                description_parts.append(f"Notable blocks visible: {', '.join(interesting_blocks)}.")
        
        return " ".join(description_parts)

    async def handle_response(self, reply: str):
        """Process AI reply and send to Minecraft bot - MAIN FIX HERE"""
        if LOG_MINECRAFT_EXECUTION:
            print(systemTColor + f"[Minecraft] Processing AI reply: {reply[:100]}..." + resetTColor)
        
        # Check bot status first
        status = await self.check_bot_status()
        if not status.get('connected') or not status.get('spawned'):
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + "[Minecraft Action] Bot not ready for actions" + resetTColor)
            return
        
        # Rate limiting to prevent spam
        current_time = time.time()
        if current_time - self.last_action_time < self.action_cooldown:
            if LOG_MINECRAFT_EXECUTION:
                print(toolTColor + f"[Minecraft Action] Rate limited - waiting {self.action_cooldown}s between actions" + resetTColor)
            return
        
        # FIXED: Send with correct field name 'text' instead of 'action'
        try:
            payload = {
                "text": reply  # Changed from "action" to "text" to match server expectations
            }
            
            response = await self._make_request('POST', '/api/action', payload, timeout=60)
            self.last_action_time = current_time
            
            if response:
                if LOG_MINECRAFT_EXECUTION:
                    status = response.get('status', 'unknown')
                    message = response.get('message', 'No message')
                    print(systemTColor + f"[Minecraft Action] Server response: {status} - {message}" + resetTColor)
                    
                    # If the server indicates it executed an action, log it
                    if response.get('action'):
                        executed_action = response.get('action')
                        print(toolTColor + f"[Minecraft Action] Server executed: {executed_action}" + resetTColor)
            else:
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + "[Minecraft Action] No response from server" + resetTColor)
                    
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Action] Error processing AI response: {e}" + resetTColor)

    async def send_action(self, action_text: str) -> Optional[Dict]:
        """Send a natural language action to the Minecraft bot for execution"""
        if LOG_MINECRAFT_EXECUTION:
            print(toolTColor + f"[Minecraft Action] Sending action: '{action_text}'" + resetTColor)
        
        try:
            # FIXED: Use correct payload format with 'text' field
            payload = {
                "text": action_text  # Changed from "action" to "text"
            }
            
            response = await self._make_request('POST', '/api/action', payload, timeout=60)
            
            if response:
                if LOG_MINECRAFT_EXECUTION:
                    status = response.get('status', 'unknown')
                    message = response.get('message', 'No message')
                    print(toolTColor + f"[Minecraft Action] Response: {status} - {message}" + resetTColor)
                return response
            else:
                if LOG_MINECRAFT_EXECUTION:
                    print(errorTColor + "[Minecraft Action] No response from bot" + resetTColor)
                return {"status": "error", "error": "No response from bot"}
                
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Action] Error sending action: {e}" + resetTColor)
            return {"status": "error", "error": f"Failed to send action: {e}"}

    async def send_minecraft_chat(self, message: str):
        """Send a message to Minecraft game chat"""
        if not PLAYING_MINECRAFT:
            return
            
        try:
            # Split long messages into chunks (Minecraft chat has character limits)
            max_length = 100  # Conservative limit for Minecraft chat
            message_chunks = []
            
            # Clean the message of any formatting that might break chat
            clean_message = re.sub(r'[^\x00-\x7F]+', '', message)  # Remove non-ASCII
            clean_message = clean_message.replace('\n', ' ').replace('\r', '')  # Remove newlines
            
            if len(clean_message) <= max_length:
                message_chunks = [clean_message]
            else:
                # Split on sentences first, then words if needed
                sentences = re.split(r'[.!?]+', clean_message)
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    if len(current_chunk + sentence) <= max_length:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            message_chunks.append(current_chunk.strip())
                        current_chunk = sentence[:max_length] + ". "
                
                if current_chunk:
                    message_chunks.append(current_chunk.strip())
            
            # Send each chunk as a separate chat message
            for i, chunk in enumerate(message_chunks):
                if not chunk.strip():
                    continue
                    
                # FIXED: Use correct payload format for chat messages with 'text' field
                chat_payload = {
                    "text": f"/say {chunk}"  # Changed from "action" to "text"
                }
                
                response = await self._make_request('POST', '/api/action', chat_payload, timeout=10)
                
                if response and response.get('status') == 'success':
                    if LOG_MINECRAFT_EXECUTION:
                        print(systemTColor + f"[Minecraft Chat] Sent message chunk {i+1}/{len(message_chunks)}" + resetTColor)
                else:
                    if LOG_MINECRAFT_EXECUTION:
                        error_msg = response.get('error', 'Unknown error') if response else 'No response'
                        print(errorTColor + f"[Minecraft Chat] Failed to send chunk {i+1}: {error_msg}" + resetTColor)
                
                # Small delay between chunks to avoid spam
                if len(message_chunks) > 1:
                    await asyncio.sleep(0.5)
                
        except Exception as e:
            if LOG_MINECRAFT_EXECUTION:
                print(errorTColor + f"[Minecraft Chat] Error sending message: {e}" + resetTColor)
    def _extract_actions_from_reply(self, reply: str) -> List[str]:
        """Extract actionable commands from AI response using comprehensive pattern matching"""
        if not reply:
            return []
        
        reply_lower = reply.lower()
        found_actions = []
        
        # Apply all action patterns
        for pattern, action_func in self.action_patterns:
            matches = re.finditer(pattern, reply_lower)
            for match in matches:
                try:
                    action = action_func(match)
                    if action and action not in found_actions:  # Avoid duplicates
                        found_actions.append(action)
                except Exception as e:
                    if LOG_MINECRAFT_EXECUTION:
                        print(errorTColor + f"[Action Pattern] Error processing pattern: {e}" + resetTColor)
        
        # Fallback: simple command mapping
        if not found_actions:
            simple_commands = {
                'follow': 'follow player',
                'come here': 'go near player',
                'come over': 'go near player',
                'stop': 'stop',
                'wait': 'stop',
                'get wood': 'gather wood',
                'mine stone': 'gather stone',
                'dig dirt': 'gather dirt',
                'attack': 'attack hostile',
                'make planks': 'craft planks',
                'place block': 'place block',
                'look around': 'look around',
            }
            
            for command, action in simple_commands.items():
                if command in reply_lower:
                    found_actions.append(action)
                    break  # Only one fallback action
        
        return found_actions

    # async def send_action(self, action_text: str) -> Optional[Dict]:
    #     """Send a natural language action to the Minecraft bot for execution"""
    #     if LOG_MINECRAFT_EXECUTION:
    #         print(toolTColor + f"[Minecraft Action] Sending action: '{action_text}'" + resetTColor)
        
    #     try:
    #         # FIXED: Use correct payload format
    #         payload = {
    #             "action": action_text
    #         }
            
    #         response = await self._make_request('POST', '/api/action', payload, timeout=60)
            
    #         if response:
    #             if LOG_MINECRAFT_EXECUTION:
    #                 status = response.get('status', 'unknown')
    #                 message = response.get('message', 'No message')
    #                 print(toolTColor + f"[Minecraft Action] Response: {status} - {message}" + resetTColor)
    #             return response
    #         else:
    #             if LOG_MINECRAFT_EXECUTION:
    #                 print(errorTColor + "[Minecraft Action] No response from bot" + resetTColor)
    #             return {"status": "error", "error": "No response from bot"}
                
    #     except Exception as e:
    #         if LOG_MINECRAFT_EXECUTION:
    #             print(errorTColor + f"[Minecraft Action] Error sending action: {e}" + resetTColor)
    #         return {"status": "error", "error": f"Failed to send action: {e}"}

    # async def send_minecraft_chat(self, message: str):
    #     """Send a message to Minecraft game chat"""
    #     if not PLAYING_MINECRAFT:
    #         return
            
    #     try:
    #         # Split long messages into chunks (Minecraft chat has character limits)
    #         max_length = 100  # Conservative limit for Minecraft chat
    #         message_chunks = []
            
    #         # Clean the message of any formatting that might break chat
    #         clean_message = re.sub(r'[^\x00-\x7F]+', '', message)  # Remove non-ASCII
    #         clean_message = clean_message.replace('\n', ' ').replace('\r', '')  # Remove newlines
            
    #         if len(clean_message) <= max_length:
    #             message_chunks = [clean_message]
    #         else:
    #             # Split on sentences first, then words if needed
    #             sentences = re.split(r'[.!?]+', clean_message)
    #             current_chunk = ""
                
    #             for sentence in sentences:
    #                 sentence = sentence.strip()
    #                 if not sentence:
    #                     continue
                        
    #                 if len(current_chunk + sentence) <= max_length:
    #                     current_chunk += sentence + ". "
    #                 else:
    #                     if current_chunk:
    #                         message_chunks.append(current_chunk.strip())
    #                     current_chunk = sentence[:max_length] + ". "
                
    #             if current_chunk:
    #                 message_chunks.append(current_chunk.strip())
            
    #         # Send each chunk as a separate chat message
    #         for i, chunk in enumerate(message_chunks):
    #             if not chunk.strip():
    #                 continue
                    
    #             # FIXED: Use correct payload format for chat messages
    #             chat_payload = {
    #                 "action": f"/say {chunk}"
    #             }
                
    #             response = await self._make_request('POST', '/api/action', chat_payload, timeout=10)
                
    #             if response and response.get('status') == 'success':
    #                 if LOG_MINECRAFT_EXECUTION:
    #                     print(systemTColor + f"[Minecraft Chat] Sent message chunk {i+1}/{len(message_chunks)}" + resetTColor)
    #             else:
    #                 if LOG_MINECRAFT_EXECUTION:
    #                     error_msg = response.get('error', 'Unknown error') if response else 'No response'
    #                     print(errorTColor + f"[Minecraft Chat] Failed to send chunk {i+1}: {error_msg}" + resetTColor)
                
    #             # Small delay between chunks to avoid spam
    #             if len(message_chunks) > 1:
    #                 await asyncio.sleep(0.5)
                
    #     except Exception as e:
    #         if LOG_MINECRAFT_EXECUTION:
    #             print(errorTColor + f"[Minecraft Chat] Error sending message: {e}" + resetTColor)
    
    async def enhance_memory_context(self, user_text: str, context_to_save: str) -> str:
        """Enhance memory context with concise Minecraft-specific information"""
        if self.last_minecraft_vision:
            # Extract key information for memory
            key_info = []
            if "Position:" in self.last_minecraft_vision:
                pos_match = re.search(r'Position: \([^)]+\)', self.last_minecraft_vision)
                if pos_match:
                    key_info.append(pos_match.group(0))
            
            if "Holding:" in self.last_minecraft_vision:
                holding_match = re.search(r'Holding: [^.]+', self.last_minecraft_vision)
                if holding_match:
                    key_info.append(holding_match.group(0))
            
            if "Players nearby:" in self.last_minecraft_vision:
                players_match = re.search(r'Players nearby: [^.]+', self.last_minecraft_vision)
                if players_match:
                    key_info.append(players_match.group(0))
            
            if key_info:
                game_context = "; ".join(key_info)
                return f"{context_to_save} [Game context: {game_context}]"
        
        return context_to_save

    def get_last_vision(self) -> str:
        """Get the last Minecraft vision data"""
        return self.last_minecraft_vision

    def set_minecraft_context_inclusion(self, enabled: bool):
        """Enable/disable inclusion of Minecraft context in prompts"""
        global INCLUDE_MINECRAFT_CONTEXT
        INCLUDE_MINECRAFT_CONTEXT = enabled
        if LOG_MINECRAFT_EXECUTION:
            print(systemTColor + f"[Minecraft Integration] Context inclusion: {'enabled' if enabled else 'disabled'}" + resetTColor)

    def get_bot_capabilities(self) -> List[str]:
        """Get list of available bot capabilities"""
        return [
            "Movement: go to coordinates, follow player, approach player",
            "Resource gathering: collect wood, stone, dirt, ores",
            "Crafting: make planks, tools from available materials",
            "Building: place blocks, break blocks",
            "Combat: attack hostile mobs, defend against threats",
            "Inventory management: drop items, equip tools",
            "Exploration: look around, scan environment, find structures",
            "Control: stop all activities, wait"
        ]

    @staticmethod
    def get_minecraft_control_variables():
        """Return current state of Minecraft-specific control variables"""
        return {
            'minecraft_controls': {
                'INCLUDE_MINECRAFT_CONTEXT': INCLUDE_MINECRAFT_CONTEXT,
            },
            'minecraft_logging': {
                'LOG_MINECRAFT_EXECUTION': LOG_MINECRAFT_EXECUTION,
            }
        }

    @staticmethod
    def set_minecraft_control_variable(variable_name: str, value: bool):
        """Dynamically set Minecraft-specific control variables at runtime"""
        if variable_name in globals():
            globals()[variable_name] = value
            print(systemTColor + f"[Minecraft Control] Set {variable_name} = {value}" + resetTColor)
        else:
            print(errorTColor + f"[Minecraft Control] Unknown variable: {variable_name}" + resetTColor)