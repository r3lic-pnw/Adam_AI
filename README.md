# AI Gaming Assistant

A sophisticated AI-powered assistant that combines voice recognition, computer vision, web search capabilities, and memory management to provide an interactive gaming and productivity companion. Built with Ollama for local LLM inference and featuring advanced multimodal capabilities.

## 🎯 Features

### Core Capabilities
- **Voice Interaction**: Real-time speech-to-text using Vosk models
- **Computer Vision**: Screenshot analysis and visual understanding
- **Memory Management**: Persistent conversation memory with semantic search
- **Web Search Integration**: Real-time information retrieval
- **Text-to-Speech**: Voice synthesis for natural conversations
- **Multiple Interaction Modes**: Text, voice, vision, gaming, and training modes
- **Screen Automation**: PyAutoGUI integration for computer control

### AI Models Support
- **Text Generation**: Configurable Ollama models (llama2, mistral, etc.)
- **Vision Analysis**: Multimodal models for screenshot understanding
- **Embedding Models**: Semantic search and memory retrieval
- **Customizable Parameters**: Temperature, tokens, penalties, and more

### Advanced Features
- **Training Mode**: Manual response approval for model fine-tuning
- **Memory Summarization**: Automatic conversation context management
- **Real-time Processing**: Asynchronous handling for smooth interactions
- **Modular Architecture**: Easy customization and extension

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher (tested on 3.13)
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 8GB (16GB+ recommended for larger models)
- **Storage**: 5GB+ free space for models and dependencies

### Required Software
1. **Ollama**: Local LLM inference engine
   - Download from: https://ollama.ai/
   - Install your preferred models (llama2, mistral, llava, etc.)

2. **VB-Audio Virtual Cable** (Windows only, for voice output):
   - Download from: https://vb-audio.com/Cable/
   - Required for TTS audio routing

3. **Vosk Speech Models** (for voice recognition):
   - Download from: https://alphacephei.com/vosk/models
   - Recommended: vosk-model-en-us-0.22 or newer

## 🚀 Installation Guide

### Step 1: Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd vtuber-ai

# Or download and extract the ZIP file
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter issues, try updating pip first:
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install and Configure Ollama
```bash
# Install Ollama (follow platform-specific instructions from ollama.ai)

# Pull recommended models
ollama pull llama2
ollama pull llava        # For vision capabilities
ollama pull mistral      # Alternative text model
ollama pull nomic-embed-text  # For embeddings

# Verify installation
ollama list
```

### Step 5: Download Vosk Speech Model
```bash
# Create models directory
mkdir -p BASE/tools/vosk-models

# Download and extract Vosk model
# Example for English model (adjust URL for your preferred language):
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip -d BASE/tools/vosk-models/
```

### Step 6: Configure the Bot
1. **Edit personality/bot_info.py**:
   ```python
   botname = "YourBotName"
   username = "YourUsername"
   textmodel = "llama2"          # Your preferred text model
   visionmodel = "llava"         # Your preferred vision model
   embedmodel = "nomic-embed-text"  # Your embedding model
   ```

2. **Edit personality/config.json** (optional):
   ```json
   {
     "ollama": {
       "endpoint": "http://localhost:11434",
       "temperature": 0.7,
       "max_tokens": 2048,
       "top_p": 0.9,
       "timeout": 120
     }
   }
   ```

3. **Customize personality/SYS_MSG.py**:
   - Edit the system_prompt variable to define your bot's personality

## 🎮 Usage Guide

### Starting the Bot
```bash
# Make sure your virtual environment is activated
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start the bot
python bot.py
```

### Interaction Modes

#### 1. Text Mode
- **Best for**: Testing, debugging, general conversation
- **Features**: Pure text interaction through terminal
- **Usage**: Type messages and press Enter

#### 2. Talk Mode
- **Best for**: Voice conversations
- **Features**: Speech-to-text + text-to-speech
- **Requirements**: Vosk model, microphone, speakers/headphones

#### 3. Vision Mode
- **Best for**: Screen analysis, visual assistance
- **Features**: Screenshot capture + AI vision analysis
- **Usage**: Ask about what's on your screen using keywords like "see", "look", "screen"

#### 4. Game Mode
- **Best for**: Gaming assistance
- **Features**: All capabilities combined for gaming scenarios
- **Usage**: Screen analysis + voice + automation capabilities

#### 5. Training Mode
- **Best for**: Fine-tuning responses
- **Features**: Manual approval of AI responses before saving to memory
- **Usage**: Review and approve/reject each response

### Available Commands

#### In-Chat Commands
- **`exit`**: Quit the application
- **`/memory`**: Display memory statistics and recent entries
- **`/summarize`**: Generate a summary of conversation history

#### Voice Triggers (in voice modes)
- **Vision keywords**: "screen", "image", "see", "look", "monitor"
- **Search keywords**: "search", "find", "look up", "web", "internet"

### Memory System
The bot maintains persistent memory across sessions:
- **Short-term**: Recent conversation context
- **Long-term**: Semantic memory with embedding-based retrieval
- **Automatic**: Saves all approved interactions
- **Searchable**: Retrieves relevant context for new queries

## 🔧 Configuration Options

### Environment Variables
Create a `.env` file in the project root:
```env
# Model Configuration
TEXT_LLM_MODEL=llama2
VISION_LLM_MODEL=llava
EMBED_MODEL=nomic-embed-text

# Ollama Settings
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2048

# Memory Settings
MAX_CONTEXT_TOKENS=500
```

### Audio Configuration
- **Input Device**: Automatically detected (default microphone)
- **Output Device**: VB-Cable for voice synthesis
- **Sample Rate**: 16kHz (optimized for Vosk)
- **Channels**: Mono audio processing

### Vision Settings
- **Screenshot Format**: PNG with base64 encoding
- **Vision Model**: Uses multimodal Ollama models (llava, bakllava, etc.)
- **Trigger Words**: Configurable vision activation keywords

## 🛠️ Troubleshooting

### Common Issues

#### "ModuleNotFoundError"
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt

# For specific missing modules:
pip install <module-name>
```

#### "PyAutoGUI was unable to import pyscreeze"
```bash
# Install Pillow explicitly
pip install pillow
```

#### "Ollama connection refused"
```bash
# Ensure Ollama is running
ollama serve

# Check if models are available
ollama list
```

#### "Vosk model not found"
```bash
# Verify model path in voice_to_text.py
# Download correct model for your language
# Ensure model is extracted to correct directory
```

#### Audio Issues (Windows)
```bash
# Install VB-Audio Virtual Cable
# Set as default playback device in Windows sound settings
# Restart application after audio driver installation
```

### Performance Optimization

#### For Better Response Times:
- Use smaller, faster models (mistral instead of llama2-70b)
- Reduce max_tokens in config
- Increase temperature for more creative but faster responses

#### For Better Quality:
- Use larger models with more parameters
- Increase max_tokens for longer responses
- Lower temperature for more consistent outputs

#### Memory Usage:
- Regularly use `/summarize` command to compress memory
- Adjust MAX_CONTEXT_TOKENS based on available RAM
- Consider using quantized models for lower memory usage

## 🎯 Advanced Usage

### Custom Model Integration
```python
# In personality/bot_info.py
textmodel = "your-custom-model"
visionmodel = "your-vision-model"

# Ensure models are available in Ollama:
# ollama pull your-custom-model
```

### Extending Functionality
- **Add new commands**: Edit the command processing section in bot.py
- **Custom search providers**: Modify BASE/tools/query.py
- **New interaction modes**: Add cases to the mode selection logic
- **Plugin system**: Extend the modular architecture in BASE/

### Integration Options
- **Gaming platforms**: Integrate with game APIs
- **Streaming software**: Connect to OBS, Streamlabs
- **Chat platforms**: Add Discord, Twitch integration
- **Automation tools**: Extend PyAutoGUI capabilities

## 📝 Notes

### Model Recommendations
- **For beginners**: llama2 (7B) + llava
- **For performance**: mistral + llava
- **For quality**: llama2-70b + bakllava (requires significant RAM)

### Privacy & Security
- All processing happens locally (no cloud API calls)
- Conversation memory stored locally in SQLite database
- No telemetry or external data transmission
- Full control over AI model behavior and responses

### Contributing
- Follow modular architecture patterns
- Test with multiple Ollama models
- Document any new dependencies in requirements.txt
- Maintain compatibility with existing personality configurations

---

**Happy chatting with your AI companion!** 🤖✨

For issues, feature requests, or contributions, please refer to the project repository or documentation.