# simple_osc_avatar_tts.py

import os
import tempfile
import pyttsx3
import sounddevice as sd
import soundfile as sf
import time
import socket
import struct
from text_to_voice import speak_through_vbcable

class SimpleOSCClient:
    """Simple OSC client without external dependencies"""
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def send_message(self, address, *args):
        """Send OSC message"""
        try:
            msg = self._create_osc_message(address, *args)
            self.sock.sendto(msg, (self.ip, self.port))
            print(f"OSC sent: {address} {args}")
        except Exception as e:
            print(f"OSC send error: {e}")
    
    def _create_osc_message(self, address, *args):
        """Create OSC message bytes"""
        # Address
        addr_bytes = address.encode('utf-8')
        addr_bytes += b'\x00' * (4 - len(addr_bytes) % 4)  # Pad to multiple of 4
        
        # Type tag
        type_tag = ','
        arg_bytes = b''
        
        for arg in args:
            if isinstance(arg, str):
                type_tag += 's'
                arg_str = arg.encode('utf-8')
                arg_str += b'\x00' * (4 - len(arg_str) % 4)  # Pad to multiple of 4
                arg_bytes += arg_str
            elif isinstance(arg, int):
                type_tag += 'i'
                arg_bytes += struct.pack('>i', arg)
            elif isinstance(arg, float):
                type_tag += 'f'
                arg_bytes += struct.pack('>f', arg)
        
        type_tag_bytes = type_tag.encode('utf-8')
        type_tag_bytes += b'\x00' * (4 - len(type_tag_bytes) % 4)  # Pad to multiple of 4
        
        return addr_bytes + type_tag_bytes + arg_bytes

class OSCAvatarTTS:
    def __init__(self, warudo_ip="127.0.0.1", warudo_port=9001):
        """
        Initialize OSC client for Warudo communication
        
        Args:
            warudo_ip: IP address of Warudo instance
            warudo_port: OSC port that Warudo is listening on
        """
        self.osc_client = SimpleOSCClient(warudo_ip, warudo_port)
        
        # Find VB-Cable device (we need the OUTPUT device to send audio TO the cable)
        # devices = sd.query_devices()
        # self.cable_index = None
        self.cable_index = 7
        
        # print("Looking for VB-Cable device...")
        # for i, device in enumerate(devices):
        #     print(f"Device {i}: {device['name']}")
        #     if "CABLE Input" in device['name'] or ("VB-Audio Virtual" in device['name'] and "Output" in device['name']):
        #         self.cable_index = i
        #         print(f"Found VB-Cable OUTPUT at index {i}: {device['name']}")
        #         break
        
        # if self.cable_index is None:
        #     print("VB-Cable OUTPUT device not found! Available devices:")
        #     for i, device in enumerate(devices):
        #         print(f"  {i}: {device['name']}")
        #     raise RuntimeError("VB-Cable OUTPUT device not found!")
    
    def speak_with_avatar(self, text, avatar_id, voice_index=1, rate=250, volume=1.0):
        """
        Send TTS to VB-Cable while signaling which avatar should animate
        
        Args:
            text: Text to speak
            avatar_id: String identifier for the avatar (e.g., "bot1", "bot2")
            voice_index: Voice selection
            rate: Speech rate
            volume: Speech volume
        """
        print(f"Speaking with avatar {avatar_id}: {text[:50]}...")
        
        # Signal Warudo which avatar should be active FIRST
        self.osc_client.send_message("/avatar/select", avatar_id)
        time.sleep(0.2)  # Small delay to ensure message is processed
        
        # Set up TTS
        # engine = pyttsx3.init()
        # voices = engine.getProperty('voices')
        
        # if voice_index < len(voices):
        #     engine.setProperty('voice', voices[voice_index].id)
        # engine.setProperty('rate', rate)
        # engine.setProperty('volume', volume)

        # Generate speech
        # temp_wav = os.path.join(tempfile.gettempdir(), f"tts_output_{avatar_id}.wav")
        # engine.save_to_file(text, temp_wav)
        # engine.runAndWait()
        speak_through_vbcable(text)

        # Load and play through VB-Cable
        # try:
        #     data, samplerate = sf.read(temp_wav, dtype='float32')

        #     # Convert to mono if needed (averaging stereo channels)
        #     if data.ndim > 1:
        #         data = data.mean(axis=1)

        #     sd.play(data, samplerate, device=self.cable_index)
            
        #     # Send speaking start signal (this will trigger your audio-based mouth animation)
        #     # self.osc_client.send_message("/speaking/start", avatar_id)
            
        #     # Play audio - your existing Warudo nodes will detect this via VB-Cable
        #     sd.wait()  # Wait for audio to finish
            
        #     # Send speaking stop signal
        #     # self.osc_client.send_message("/speaking/stop", avatar_id)
            
        # except Exception as e:
        #     print(f"Error during TTS playback: {e}")
        # finally:
        #     # Clean up
        #     if os.path.exists(temp_wav):
        #         os.remove(temp_wav)
        
        # return f"TTS executed for avatar {avatar_id}"

# Global instance
tts_system = None

def initialize_tts_system(warudo_ip="127.0.0.1", warudo_port=9001):
    """Initialize the TTS system"""
    global tts_system
    tts_system = OSCAvatarTTS(warudo_ip, warudo_port)

# def bot_speak(text, bot_name, voice_index=1, rate=250):
#     """Convenience function for bot speech"""
#     if tts_system is None:
#         initialize_tts_system()
#     return tts_system.speak_with_avatar(text, bot_name, voice_index, rate)

# Specific bot functions
def alice_speak(text):
    # return bot_speak(text, "bot1", voice_index=1, rate=200)
    return speak_through_vbcable(text)

def bob_speak(text):
    # return bot_speak(text, "bot2", voice_index=2, rate=250)
    speak_through_vbcable(text)
def charlie_speak(text):
    # return bot_speak(text, "bot3", voice_index=0, rate=180)
    speak_through_vbcable(text)
def diana_speak(text):
    # return bot_speak(text, "bot4", voice_index=3, rate=220)
    speak_through_vbcable(text)
# Simple test functions
def test_osc_only():
    """Test OSC messaging without TTS"""
    client = SimpleOSCClient("127.0.0.1", 9001)
    
    print("Testing OSC avatar selection...")
    bots = ["bot1", "bot2", "bot3", "bot4"]
    
    for bot in bots:
        print(f"Selecting {bot}")
        client.send_message("/avatar/select", bot)
        # time.sleep(1)
        
        # Test speaking signals
        # print(f"  Testing speaking start/stop for {bot}")
        # client.send_message("/speaking/start", bot)
        time.sleep(2)
        # client.send_message("/speaking/stop", bot)
        # time.sleep(1)
    
    print("OSC test complete!")

def test_sequential_speech():
    """Test sequential speech with different bots"""
    print("Testing sequential bot speech...")
    
    test_phrases = [
        ("Alice", "Hello, I'm Alice speaking first."),
        ("Bob", "Hi Alice, this is Bob responding."), 
        ("Charlie", "Charlie here, joining the conversation."),
        ("Diana", "And I'm Diana, nice to meet everyone!")
    ]
    
    speaker_functions = {
        "Alice": alice_speak,
        "Bob": bob_speak,
        "Charlie": charlie_speak, 
        "Diana": diana_speak
    }
    
    for speaker, phrase in test_phrases:
        print(f"\n{speaker} is about to speak...")

        speaker_functions[speaker](phrase)
        time.sleep(2)  # Brief pause between speakers

def list_audio_devices():
    """List all available audio devices"""
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        device_type = "Input" if device['max_input_channels'] > 0 else "Output"
        if device['max_input_channels'] > 0 and device['max_output_channels'] > 0:
            device_type = "Input/Output"
        print(f"{i}: {device['name']} ({device_type})")
    print()

# Example usage
if __name__ == "__main__":
    print("Simple OSC Avatar TTS System")
    print("============================")
    
    # List available audio devices
    # list_audio_devices()
    
    # Test OSC connectivity first
    print("\n1. Testing OSC messages only...")
    test_osc_only()
    
    # Test full TTS system
    print("\n2. Testing full TTS system...")
    test_sequential_speech()