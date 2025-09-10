#!/usr/bin/env python3
"""
Warudo Avatar Animation Script - Refactored with WarudoManager

This script centralizes Warudo avatar controls and animation handling.
"""

import time
import json
import threading
from typing import Dict, List
import uuid

# WebSocket imports
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    print("Error: websocket-client not installed.")
    print("Install with: pip install websocket-client")
    WEBSOCKET_AVAILABLE = False
    exit(1)

# Keyword mapping: words → Warudo command
animation_keywords = {
    # Emotions
    'happy': 'happy',
    'smile': 'smile',
    'smiling': 'smile',
    'glad': 'happy',
    'joy': 'happy',
    'joyful': 'happy',
    'cheerful': 'happy',
    'excited': 'happy',
    'pleased': 'smile',
    'delighted': 'happy',
    'sad': 'sad',
    'upset': 'sad',
    'disappointed': 'sad',
    'angry': 'angry',
    'mad': 'angry',
    'frustrated': 'angry',
    'annoyed': 'angry',
    'surprised': 'surprised',
    'shocked': 'surprised',
    'amazed': 'surprised',
    'astonished': 'surprised',
    'confused': 'confused',
    'puzzled': 'confused',
    'perplexed': 'confused',
    'wink': 'wink',
    'winking': 'wink',
    'blush': 'blush',
    'blushing': 'blush',
    'embarrassed': 'blush',
    'neutral': 'neutral',

    # Actions/Animations
    'wave': 'wave',
    'waving': 'wave',
    'hello': 'wave',
    'hi': 'wave',
    'goodbye': 'wave',
    'bye': 'wave',
    'nod': 'nod',
    'nodding': 'nod',
    'yes': 'nod',
    'agree': 'nod',
    'shake': 'shake_head',
    'no': 'shake_head',
    'disagree': 'shake_head',
    'bow': 'bow',
    'bowing': 'bow',
    'thank': 'bow',
    'thanks': 'bow',
    'dance': 'dance',
    'dancing': 'dance',
    'clap': 'clap',
    'clapping': 'clap',
    'applaud': 'clap',
    'point': 'point',
    'pointing': 'point',
    'think': 'think',
    'thinking': 'think',
    'wonder': 'think',
    'ponder': 'think',
    'thumbs up': 'thumbs_up',
    'good job': 'thumbs_up',
    'well done': 'thumbs_up',
    'great': 'thumbs_up',
    'awesome': 'thumbs_up',
    'shrug': 'shrug',
    'shrugging': 'shrug',
    "don't know": 'shrug',
    'dunno': 'shrug',
    'laugh': 'laugh',
    'laughing': 'laugh',
    'lol': 'laugh',
    'haha': 'laugh',
    'funny': 'laugh',
    'cat': 'cat',
    'meow': 'cat',
    'kitty': 'cat'
}


class WarudoWebSocketController:
    """Controller for sending commands to Warudo via WebSocket API"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190"):
        self.websocket_url = websocket_url
        self.ws = None
        self.ws_connected = False
        self.connection_lock = threading.Lock()

        self.available_emotions = [
            'smile', 'happy', 'sad', 'angry', 'surprised',
            'confused', 'wink', 'blush', 'neutral'
        ]
        self.available_animations = [
            'wave', 'nod', 'shake_head', 'bow', 'dance',
            'clap', 'point', 'think', 'thumbs_up', 'shrug',
            'laugh', 'upset', 'cat'
        ]

    def connect_websocket(self, timeout: float = 5.0) -> bool:
        """Connect to Warudo WebSocket server"""
        with self.connection_lock:
            if self.ws_connected:
                return True
            try:
                def on_message(ws, message):
                    print(f"WebSocket received: {message}")

                def on_error(ws, error):
                    print(f"WebSocket error: {error}")
                    self.ws_connected = False

                def on_close(ws, close_status_code, close_msg):
                    print("WebSocket connection closed")
                    self.ws_connected = False

                def on_open(ws):
                    print("WebSocket connection opened")
                    self.ws_connected = True

                self.ws = websocket.WebSocketApp(
                    self.websocket_url,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                wst = threading.Thread(target=self.ws.run_forever, daemon=True)
                wst.start()

                start_time = time.time()
                while not self.ws_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)

                return self.ws_connected
            except Exception as e:
                print(f"Failed to connect WebSocket: {e}")
                return False

    def send_websocket_command(self, command: Dict) -> bool:
        if not self.ws or not self.ws_connected:
            print("WebSocket not connected")
            return False
        try:
            message = json.dumps(command)
            self.ws.send(message)
            print(f"WebSocket sent: {message}")
            return True
        except Exception as e:
            print(f"Failed to send WebSocket command: {e}")
            return False

    def send_single_command(self, command: str) -> bool:
        """Send a single word command (emotion or animation)"""
        command = command.strip().lower()
        if command in self.available_emotions:
            return self.send_websocket_command({'action': 'emotion', 'data': command})
        elif command in self.available_animations:
            return self.send_websocket_command({'action': 'animation', 'data': command})
        else:
            print(f"Unknown command: {command}")
            return False

    def get_available_commands(self) -> Dict[str, List[str]]:
        return {'emotions': self.available_emotions, 'animations': self.available_animations}


class WarudoManager:
    """High-level manager for Warudo integration."""

    def __init__(self, websocket_url: str, auto_connect: bool = True, timeout: float = 5.0):
        self.controller = WarudoWebSocketController(websocket_url)
        self.animation_keywords = animation_keywords
        self.enabled = True
        if auto_connect:
            self.connect(timeout)

    def connect(self, timeout: float = 5.0) -> bool:
        success = self.controller.connect_websocket(timeout=timeout)
        if success:
            print("[Warudo] Connected successfully.")
        else:
            print("[Warudo] Connection failed.")
        return success

    def detect_and_send_animations(self, text: str):
        """Detect animation keywords in text and trigger Warudo commands."""
        if not self.enabled or not self.controller:
            return
        text_lower = text.lower()
        sent = set()
        for keyword, command in self.animation_keywords.items():
            if keyword in text_lower and command not in sent:
                print(f"[Warudo] Detected '{keyword}' → '{command}'")
                if self.controller.send_single_command(command):
                    sent.add(command)
        if sent:
            print(f"[Warudo] Sent {len(sent)} animation(s): {', '.join(sent)}")

    def handle_command(self, command: str) -> bool:
        """Handle CLI-like commands for Warudo."""
        cmd = command.lower().strip()
        if cmd == "/warudo_connect":
            return self.connect()
        elif cmd == "/warudo_test":
            test_commands = ['happy', 'wave', 'nod', 'thumbs_up']
            for c in test_commands:
                self.controller.send_single_command(c)
                time.sleep(1)
            return True
        elif cmd == "/warudo_commands":
            cmds = self.controller.get_available_commands()
            print("[Warudo] Emotions:", ", ".join(cmds['emotions']))
            print("[Warudo] Animations:", ", ".join(cmds['animations']))
            return True
        elif cmd.startswith("/warudo_send "):
            c = cmd.split(" ", 1)[1]
            return self.controller.send_single_command(c)
        elif cmd == "/warudo_keywords":
            for k, v in sorted(self.animation_keywords.items()):
                print(f"  '{k}' -> {v}")
            return True
        return False


if __name__ == "__main__":
    if not WEBSOCKET_AVAILABLE:
        exit(1)
    # Simple demo
    wm = WarudoManager("ws://127.0.0.1:19190")
    wm.detect_and_send_animations("I am so happy, let’s wave and laugh together!")
