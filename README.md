# Ollama AI Game Assistant - Complete Setup Guide

## Table of Contents

- [What Is This?](#what-is-this)
- [Key Features](#key-features)
  - [Core Functionality](#core-functionality)
  - [Gaming Features](#gaming-features)
  - [Technical Features](#technical-features)
- [What You'll Need](#what-youll-need)
  - [Required Software](#required-software)
  - [System Requirements](#system-requirements)
  - [Optional Hardware](#optional-hardware)
- [Installation Guide](#installation-guide)
  - [Step 1: Install Core Dependencies](#step-1-install-core-dependencies)
  - [Step 2: Download the Assistant](#step-2-download-the-assistant)
  - [Step 3: Set Up Python Environment](#step-3-set-up-python-environment)
  - [Step 4: Set Up Minecraft Bot (Optional)](#step-4-set-up-minecraft-bot-optional)
  - [Step 5: Configure the Assistant](#step-5-configure-the-assistant)
- [How to Start the Assistant](#how-to-start-the-assistant)
  - [Quick Start (Recommended)](#quick-start-recommended)
  - [Minecraft Mode](#minecraft-mode)
  - [Manual Start](#manual-start)
  - [Mobile Mode (Advanced)](#mobile-mode-advanced)
- [Understanding the Interface](#understanding-the-interface)
  - [GUI Mode](#gui-mode)
  - [Terminal Mode](#terminal-mode)
  - [Voice Mode](#voice-mode)
- [Available Commands](#available-commands)
  - [Basic Commands](#basic-commands)
  - [Feature Toggles](#feature-toggles)
  - [Memory Commands](#memory-commands)
  - [Minecraft Commands](#minecraft-commands-when-in-minecraft-mode)
  - [Preset Configurations](#preset-configurations)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Customizing Your Assistant](#customizing-your-assistant)
  - [Personality Configuration](#personality-configuration)
  - [System Prompts](#system-prompts)
  - [Avatar Setup with Warudo (Advanced)](#avatar-setup-with-warudo-advanced)
- [Performance Optimization](#performance-optimization)
  - [For Lower-End Computers](#for-lower-end-computers)
  - [For High-End Computers](#for-high-end-computers)
- [File Structure Explained](#file-structure-explained)
- [Memory Management System](#memory-management-system)
  - [Overview](#overview-1)
  - [Memory Architecture](#memory-architecture)
  - [Memory Components Explained](#memory-components-explained)
  - [Memory Search Intelligence](#memory-search-intelligence)
  - [Memory Commands](#memory-commands-1)
  - [Creating Custom Knowledge Bases](#creating-custom-knowledge-bases)
  - [Memory Performance Optimization](#memory-performance-optimization)
  - [Memory System Troubleshooting](#memory-system-troubleshooting)
  - [Advanced Memory Features](#advanced-memory-features)
- [Android Mobile Version Setup](#android-mobile-version-setup)
  - [Overview](#overview-2)
  - [Mobile Version Features](#mobile-version-features)
  - [Installation Requirements](#installation-requirements)
  - [Step-by-Step Mobile Installation](#step-by-step-mobile-installation)
  - [Mobile-Specific Configuration](#mobile-specific-configuration)
  - [Usage Instructions](#usage-instructions)
  - [Intelligent Features](#intelligent-features)
  - [Performance Optimization](#performance-optimization-1)
  - [Troubleshooting Mobile Issues](#troubleshooting-mobile-issues)
  - [Mobile-Specific Limitations](#mobile-specific-limitations)
  - [Cross-Device Memory Synchronization](#cross-device-memory-synchronization)

---

## What Is This?

This is a local AI assistant designed for gaming and general interaction. It runs entirely on your computer using Ollama (a local AI system) and includes features like voice chat, internet search, avatar animations, memory storage, and Minecraft integration. Think of it as your personal AI companion that can see your screen, remember conversations, search the web, and even play Minecraft with you!

## Key Features

### Core Functionality
- **Text and Voice Input**: Type messages or speak naturally to your AI assistant
- **Text-to-Speech**: The AI can speak back to you using your computer's audio system
- **Internet Search**: The AI can search the web for current information
- **Computer Vision**: The AI can see and analyze your computer screen
- **Memory System**: Remembers your conversations and can recall past interactions

### Gaming Features
- **Minecraft Integration**: The AI can control a Minecraft bot, play alongside you, and chat in-game
- **Avatar Animations**: If you use Warudo (VTuber software), the AI can animate an avatar based on emotions
- **Training Mode**: The AI can research topics and build knowledge for better assistance

### Technical Features
- **Local Processing**: Everything runs on your computer - no data sent to external services
- **Multiple Interfaces**: GUI application, terminal mode, and mobile support via Termux
- **Modular Design**: Enable or disable features as needed
- **Memory Management**: Both short-term daily memory and long-term summarized knowledge

## What You'll Need

### Required Software
1. **Python 3.10 or newer** - The programming language that runs the assistant
2. **Node.js and npm** - Required for the Minecraft bot functionality
3. **Ollama** - The local AI system that powers the assistant
4. **Git** (optional) - For downloading and updating the code

### System Requirements
- **RAM**: At least 8GB recommended (16GB for better performance)
- **Storage**: 10-20GB free space for AI models and dependencies
- **Operating System**: Windows 10/11, macOS, or Linux
- **Internet**: Required for initial setup and web search features

### Optional Hardware
- **Microphone**: For voice input
- **Good CPU/GPU**: Better hardware = faster AI responses
- **Multiple Monitors**: Helpful for running both the assistant and other applications

## Installation Guide

### Step 1: Install Core Dependencies

#### Install Python
1. Go to [python.org](https://python.org) and download Python 3.10 or newer
2. During installation, **check the box** that says "Add Python to PATH"
3. Open Command Prompt and type `python --version` to verify installation

#### Install Node.js
1. Go to [nodejs.org](https://nodejs.org) and download the LTS version
2. Install with default settings
3. Open Command Prompt and type `node --version` and `npm --version` to verify

#### Install Ollama
1. Go to [ollama.ai](https://ollama.ai) and download Ollama for your operating system
2. Install and start Ollama
3. Download required AI models by opening Command Prompt and typing:
   ```
   ollama pull llama3.1:8b
   ollama pull llava:7b
   ollama pull nomic-embed-text
   ```
   (These downloads may take 15-30 minutes depending on your internet speed)

### Step 2: Download the Assistant

#### Option A: Download as ZIP
1. Download the project as a ZIP file and extract it to a folder like `C:\OllamaAI\`

#### Option B: Use Git (recommended)
1. Open Command Prompt
2. Navigate to where you want to install (e.g., `cd C:\`)
3. Type: `git clone [repository-url] OllamaAI`
4. Type: `cd OllamaAI`

### Step 3: Set Up Python Environment

1. Open Command Prompt in your project folder
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - **Windows**: `venv\Scripts\activate`
   - **macOS/Linux**: `source venv/bin/activate`
4. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

### Step 4: Set Up Minecraft Bot (Optional)

If you want Minecraft integration:
1. Navigate to the MC_BOT folder: `cd BASE\MC_BOT`
2. Install Node.js dependencies: `npm install`
3. Return to the main folder: `cd ..\..`

### Step 5: Configure the Assistant

1. Create a `.env` file in the main folder with these settings:
   ```
   OLLAMA_ENDPOINT=http://localhost:11434
   OLLAMA_NUM_PARALLEL=2
   MC_HOST=localhost
   MC_PORT=25565
   BOT_NAME=Anna
   ```

2. Edit `personality/config.json` to customize your assistant's name and behavior

## How to Start the Assistant

### Quick Start (Recommended)
1. Double-click `gui_start.bat` - This launches the GUI interface with all features

### Minecraft Mode
1. First, make sure you have a Minecraft server running on your computer
2. Double-click `mc_start.bat` - This starts the Minecraft server and spawns the AI bot
3. Then run `gui_start.bat` to start the assistant interface

### Manual Start
1. Open Command Prompt in the project folder
2. Activate the virtual environment: `venv\Scripts\activate`
3. Run the main bot: `python BASE/bot.py`

### Mobile Mode (Advanced)
If you have an Android device with Termux:
1. Install Termux from F-Droid (not Google Play Store)
2. Copy the mobile version files to your device
3. Follow the mobile setup instructions in the Termux terminal

## Understanding the Interface

### GUI Mode
- **Chat Window**: Type messages to the AI or see conversation history
- **Terminal Output**: Shows what the AI is thinking and doing
- **Control Panel**: Toggle features on/off
- **Voice Indicators**: Shows when voice input is active

### Terminal Mode
- Type messages and press Enter
- Use `/help` to see available commands
- Use `/exit` to quit

### Voice Mode
- Speak naturally when the microphone is active
- The AI will respond with both text and speech
- Voice recognition works best in quiet environments

## Available Commands

### Basic Commands
- `/help` - Show all available commands
- `/settings` or `/status` - Show current configuration
- `/exit` - Close the assistant

### Feature Toggles
- `/toggle_vision` - Enable/disable screen analysis
- `/toggle_search` - Enable/disable web search
- `/toggle_memory` - Enable/disable memory search
- `/toggle_minecraft` - Enable/disable Minecraft mode
- `/toggle_animations` - Enable/disable avatar animations
- `/toggle_speech` - Enable/disable text-to-speech

### Memory Commands
- `/memory_stats` - Show memory usage statistics
- `/search_memory <query>` - Search through conversation history
- `/clear_memory` - Reset conversation memory (use carefully!)
- `/summarize` - Create summary of recent conversations

### Minecraft Commands (when in Minecraft mode)
- `/minecraft_status` - Check if the Minecraft bot is connected
- The AI can understand commands like "go to the nearest tree" or "collect wood"

### Preset Configurations
- `/presets` - List available configuration presets
- `/preset minimal` - Basic features only (faster, less memory)
- `/preset standard` - Balanced features (recommended)
- `/preset full_features` - All features enabled (requires good hardware)
- `/preset minecraft` - Optimized for Minecraft gameplay
- `/preset group_chat` - Optimized for group conversations

## Troubleshooting Common Issues

### "Model not found" errors
1. Make sure Ollama is running (check system tray)
2. Download required models: `ollama pull llama3.1:8b`
3. Check that `OLLAMA_ENDPOINT` in `.env` file is correct

### Voice input not working
1. Check microphone permissions in Windows settings
2. Verify microphone is working in other applications
3. Try restarting the assistant

### Slow responses
1. Use smaller AI models if your hardware is limited
2. Try the `/preset minimal` configuration
3. Close other resource-intensive applications
4. Consider upgrading RAM or using a computer with better GPU

### Minecraft bot won't connect
1. Make sure Minecraft server is running first
2. Check that the server allows bots (some servers block them)
3. Verify MC_HOST and MC_PORT settings in `.env` file
4. Try using Minecraft version 1.16 or earlier

### Python/Node.js errors
1. Make sure you activated the virtual environment: `venv\Scripts\activate`
2. Try reinstalling dependencies: `pip install -r requirements.txt`
3. For Node.js issues: `cd BASE\MC_BOT` then `npm install`

### Memory issues
1. Use `/memory_stats` to check memory usage
2. Use `/clear_memory` if memory becomes corrupted
3. Restart the assistant to reset temporary memory

## Customizing Your Assistant

### Personality Configuration
Edit `personality/bot_info.py` to change:
- Assistant's name
- Response style
- Default behaviors

### System Prompts
Edit files in `personality/` folder to modify:
- How the AI responds
- What knowledge it has
- Behavioral patterns

### Avatar Setup with Warudo (Advanced)

Warudo is VTuber software that allows you to animate a 3D avatar in real-time. This assistant includes pre-configured avatar files and can automatically animate your avatar based on conversation emotions.

#### What's Included
Your installation includes these avatar files in `personality/avatar/`:
- **Anna.vrm** - The 3D avatar model file (VRM format)
- **Anna.json** - Warudo blueprint configuration file
- **Anna Animations.json** - Pre-defined animation sequences
- **Anna_model.vroid** - Original VRoid Studio project file (for editing)

#### Setting Up Warudo Integration

**Step 1: Install Warudo**
1. Download Warudo from [warudo.app](https://warudo.app) (requires purchase)
2. Install and launch Warudo
3. Complete the initial setup wizard

**Step 2: Load the Avatar**
1. In Warudo, go to the **Scene** tab
2. Click **Add Asset** → **Character**
3. In the Character settings, click **Model** → **Browse**
4. Navigate to your project folder: `personality/avatar/Anna.vrm`
5. Select the Anna.vrm file and click **Open**
6. The avatar should appear in the scene

**Step 3: Import Animation Blueprint**
1. In Warudo, go to **File** → **Import Blueprint**
2. Navigate to `personality/avatar/Anna.json`
3. Click **Open** to import the pre-configured setup
4. This loads camera angles, lighting, and animation triggers

**Step 4: Configure OSC Communication**
1. In Warudo, go to **Assets** tab
2. Find **OSC Receiver** in the assets list
3. Set the **Port** to **39539** (default for this assistant)
4. Set **IP Address** to **127.0.0.1** (localhost)
5. Click **Enable** to activate OSC reception

**Step 5: Load Animation Sequences**
1. Go to **Assets** → **Animation Controller**
2. Click **Import Animations**
3. Select `personality/avatar/Anna Animations.json`
4. This loads pre-defined animations for different emotions and actions

**Step 6: Test the Connection**
1. In your AI assistant, use the command `/toggle_animations` to enable animations
2. Use `/warudo_status` to check connection status
3. Try saying something emotional like "I'm so excited!" - the avatar should react
4. Use `/warudo_connect` if the connection fails

#### How Avatar Animations Work

The assistant automatically detects emotions and keywords in conversations and sends animation commands to Warudo:

**Emotional Animations:**
- **Happy/Excited**: "great", "awesome", "love", "excited" → Joy animation
- **Sad/Disappointed**: "sad", "disappointed", "sorry" → Sad animation  
- **Surprised**: "wow", "amazing", "incredible" → Surprise animation
- **Confused**: "confused", "don't understand", "what" → Confusion animation
- **Angry/Frustrated**: "angry", "frustrated", "annoying" → Anger animation

**Action Animations:**
- **Greeting**: "hello", "hi", "good morning" → Wave animation
- **Farewell**: "goodbye", "bye", "see you later" → Goodbye animation
- **Thinking**: "hmm", "let me think", "considering" → Thinking pose
- **Explaining**: "basically", "so what happens is" → Gesture animation

**Gaming-Specific Animations:**
- **Victory**: "won", "victory", "success" → Celebration animation
- **Defeat**: "lost", "failed", "died" → Disappointment animation
- **Combat**: "fighting", "battle", "attack" → Action pose

#### Customizing Your Avatar

**Editing the Avatar Model:**
1. Open **VRoid Studio** (free software from Pixiv)
2. Load `personality/avatar/Anna_model.vroid`
3. Modify hair, clothing, face, body as desired
4. Export as .vrm file and replace `Anna.vrm`

**Adding Custom Animations:**
1. In Warudo, record new animation sequences
2. Export them and add to `Anna Animations.json`
3. Update the animation detection keywords in `personality/controls.py`

**Modifying Animation Triggers:**
Edit the animation detection logic by modifying these files:
- `BASE/tools/animate.py` - Core animation detection
- `personality/controls.py` - Animation keywords and settings

#### Troubleshooting Avatar Issues

**Avatar doesn't appear:**
- Check that Anna.vrm file isn't corrupted
- Ensure Warudo supports VRM 0.0 format
- Try importing a different VRM file to test Warudo functionality

**Animations don't trigger:**
- Use `/warudo_status` to check connection
- Verify OSC port 39539 is not blocked by firewall
- Check that OSC Receiver is enabled in Warudo
- Try `/warudo_connect` to reconnect

**Poor animation performance:**
- Reduce Warudo's render quality settings
- Close other resource-intensive applications
- Use simpler lighting in Warudo scene
- Disable real-time shadows if performance is poor

**Connection keeps dropping:**
- Check that Warudo is running before starting the assistant
- Verify no other software is using OSC port 39539
- Try restarting both Warudo and the assistant

#### Advanced Warudo Features

**Live Streaming Setup:**
- Configure OBS Studio to capture Warudo's output
- Use virtual camera feature for video calls
- Set up greenscreen background for easy compositing

**Multiple Expressions:**
- The avatar includes multiple facial expressions
- Expressions change automatically based on conversation tone
- Manual expression control available via `/warudo` commands

**Camera Controls:**
- Pre-configured camera angles for different situations
- Automatic camera switching during conversations
- Manual camera control via Warudo interface

**Background and Effects:**
- Custom backgrounds can be loaded in Warudo
- Particle effects and lighting can enhance the presentation
- Scene transitions available for different conversation modes

The avatar system adds significant visual appeal to interactions and is particularly popular for content creation, streaming, or just making conversations more engaging. While setup requires some initial configuration, the pre-built files make the process much simpler than creating everything from scratch.

## Performance Optimization

### For Lower-End Computers
- Use `/preset minimal`
- Reduce `OLLAMA_NUM_PARALLEL` to 1 in `.env`
- Use smaller AI models
- Disable voice features if not needed

### For High-End Computers
- Use `/preset full_features`
- Increase `OLLAMA_NUM_PARALLEL` to 4 or higher
- Use larger, more capable AI models
- Enable all vision and search features

## File Structure Explained

```
Project Root/
├── gui_start.bat          # Quick start for GUI mode
├── mc_start.bat           # Quick start for Minecraft mode
├── requirements.txt       # Python dependencies list
├── .env                   # Configuration settings
├── BASE/                  # Core assistant code
│   ├── bot.py            # Main assistant program
│   ├── core/             # Core functionality
│   ├── tools/            # Voice, vision, animation tools
│   ├── memory_methods/   # Memory and learning systems
│   └── MC_BOT/           # Minecraft integration
├── personality/          # Assistant personality and config
│   ├── bot_info.py       # Name, colors, model settings
│   ├── config.json       # Behavior configuration
│   ├── memory/           # Stored conversations
│   └── avatar/           # Avatar files for animations
├── models/               # Voice recognition models
└── venv/                 # Python virtual environment
```

# Memory Management System

## Overview

This AI assistant uses a sophisticated multi-layered memory architecture that goes far beyond simple chat history. The memory system consists of three distinct components that work together to provide contextually aware and knowledgeable responses:

1. **Short-term Memory** - Individual chat messages (not embedded)
2. **Long-term Memory** - Conversation summaries (embedded for search)
3. **Knowledge Base** - Pre-embedded reference materials (enhanced chunking)

## Memory Architecture

### Three-Layer Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│ 1. SHORT-TERM (memory.json)                                │
│    • Individual chat messages                              │
│    • Recent conversations (last 50 entries)               │
│    • NOT embedded - stored as raw text                    │
│    • Used for immediate context                           │
│                                                           │
│ 2. LONG-TERM (embeddings.json)                           │
│    • AI-generated conversation summaries                  │
│    • Embedded using semantic search                       │
│    • Created automatically when memory gets full          │
│    • Searchable by topic/content similarity              │
│                                                           │
│ 3. KNOWLEDGE BASE (base_memory/*.json)                    │
│    • Pre-embedded reference materials                     │
│    • Enhanced chunking with metadata                      │
│    • Minecraft guides, tutorials, strategies             │
│    • Categorized by topic (combat, crafting, etc.)      │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
personality/
├── memory/
│   ├── memory.json           # Recent chat entries (not embedded)
│   └── embeddings.json       # Conversation summaries (embedded)
└── memory_base/
    ├── base_files/           # Source documents for embedding
    └── base_memory/          # Pre-embedded knowledge chunks
        ├── minecraft_guide_embeddings.json
        ├── tutorial_embeddings.json
        └── [other knowledge files]
```

## Memory Components Explained

### 1. Short-Term Memory (memory.json)

**Purpose**: Stores recent individual messages for immediate conversation context.

**Content**: Raw chat entries between user and assistant, stored as JSON objects:
```json
{
  "role": "user",
  "content": "How do I craft a pickaxe?",
  "timestamp": "Tuesday, January 14, 2025 at 03:42 PM UTC"
}
```

**Key Features**:
- Stores last 50+ conversation entries by default
- NOT embedded (no vector search)
- Used for maintaining conversation flow
- Automatically managed (older entries removed when full)
- Provides immediate context for current conversation

**Why Not Embedded**: Individual chat messages are kept as raw text because:
- Immediate context doesn't need semantic search
- Preserves exact conversation flow
- Faster access for recent context
- Prevents over-embedding of casual conversation

### 2. Long-Term Memory (embeddings.json)

**Purpose**: Stores AI-generated summaries of past conversations for topic-based retrieval.

**Content**: Embedded conversation summaries created by the summarizer:
```json
{
  "text": "User asked about diamond mining strategies. Discussed optimal Y-levels (Y-11 to Y-15), branch mining techniques, and safety precautions for lava. Covered tool durability and enchantments.",
  "embedding": [0.234, -0.567, 0.123, ...],
  "metadata": {
    "entry_type": "conversation_summary",
    "source_type": "personal",
    "summary_date": "Tuesday, January 14, 2025 at 04:15 PM UTC"
  }
}
```

**Automatic Summarization Process**:
1. When short-term memory fills up (50+ entries)
2. Groups entries into conversation chunks
3. Uses LLM to create concise summaries
4. Embeds summaries using `nomic-embed-text` model
5. Archives original entries to save memory

**Search Capabilities**:
- Semantic similarity search using vector embeddings
- Triggered by queries like "remember when we talked about..."
- Finds relevant past conversations by topic, not exact words

### 3. Knowledge Base (base_memory/)

**Purpose**: Pre-embedded reference materials providing expert knowledge on specific topics.

**Enhanced Chunking System**: Uses sophisticated content processing with metadata:

```json
{
  "text": "Diamond ore generates most commonly at Y-levels -50 to -64, with peak generation at Y-58. Use iron pickaxe or better to mine diamonds. Always dig cautiously near lava levels.",
  "embedding": [0.845, -0.234, 0.678, ...],
  "metadata": {
    "source_file": "minecraft_guide_embeddings.json",
    "source_type": "base_memory",
    "main_section_title": "Mining and Resources",
    "section_level": 2,
    "context_path": "Mining Guide > Diamond Mining > Optimal Locations",
    "chunk_type": "mining",
    "keywords": ["diamond", "mining", "Y-level", "pickaxe"],
    "sections_included": ["Diamond Locations", "Mining Tools"]
  }
}
```

**Chunk Categories**:
- **combat**: Fighting mobs, weapons, armor strategies
- **crafting**: Recipes, crafting tables, item creation
- **mining**: Ore locations, mining techniques, tools
- **farming**: Crops, animals, food production
- **building**: Construction, materials, architecture
- **survival**: Health, hunger, basic needs
- **exploration**: Biomes, structures, navigation
- **progression**: Game advancement, goals, upgrades

**Smart Relevance Scoring**: Combines semantic similarity with metadata:
- Base similarity from vector comparison
- Category matching bonuses (e.g., combat query + combat chunk)
- Keyword overlap scoring
- Section authority weighting
- Final relevance score determines result ranking

## Memory Search Intelligence

### Query Classification

The system automatically analyzes queries to determine search strategy:

```python
# Examples of query classification:
"how to fight zombies" → Category: combat, Confidence: 0.8
"craft a pickaxe" → Category: crafting, Confidence: 0.9
"remember our conversation about mining" → Triggers: long-term search
```

### Search Prioritization

1. **Knowledge-Seeking Queries**: Search knowledge base first
   - "How to...", "What is...", "Best way to..."
   - Minecraft-specific terms detected

2. **Historical Queries**: Search conversation summaries
   - "Remember when...", "We talked about..."
   - Personal context needed

3. **Recent Context**: Use short-term memory
   - Follow-up questions
   - Continuation of current topic

### Enhanced Search Features

**Multi-Source Results**: Combines different memory types:
```
=== RELEVANT KNOWLEDGE ===
Knowledge Base:
- Diamond ore generates at Y-11 to Y-15... [Mining - Diamond Guide] (relevance: 0.92)

Personal History Summaries:
- User previously asked about efficient mining... [Summary] (relevance: 0.78)

=== RECENT CONVERSATIONS ===
[Tuesday, Jan 14, 2025 at 03:40 PM] User: I want to start mining
[Tuesday, Jan 14, 2025 at 03:41 PM] Assistant: I can help you get started...
```

## Memory Commands

### Basic Memory Operations
- `/memory_stats` - Show detailed memory statistics
- `/search_memory <query>` - Search all memory types
- `/clear_memory` - Reset personal memory (preserves knowledge base)

### Advanced Memory Management
- `/toggle_memory` - Enable/disable memory search
- `/summarize` - Manually trigger conversation summarization
- `/reload_base_memory` - Refresh knowledge base from files

### Memory Search Variants
- `/search_base <query>` - Search only knowledge base
- `/search_personal <query>` - Search only conversation history
- `/minecraft_help <query>` - Specialized Minecraft knowledge search

### Preset Configurations for Memory
- `/preset minimal` - Basic memory only (faster)
- `/preset standard` - Balanced memory usage
- `/preset full_features` - All memory systems active

## Creating Custom Knowledge Bases

### Document Embedding Process

Use the included `embed-document.py` script to create your own knowledge bases:

```bash
# 1. Place documents in the base_files directory
cp your_guide.txt personality/memory_base/base_files/

# 2. Run the embedding script
python BASE/memory_methods/embed_document.py

# 3. Embeddings are automatically saved to base_memory/
```

**Supported File Types**: .txt, .md, .py, .js, .html, .css, .json, .xml, .csv, .log

**Chunking Strategy**:
- Splits documents into 1000-character chunks with 200-character overlap
- Preserves sentence boundaries when possible
- Creates hierarchical metadata for better search
- Generates keywords and context paths automatically

### Custom Chunking Configuration

For specialized content, modify the chunking parameters in `embed-document.py`:

```python
# Chunk size configuration
chunk_size = 1000      # Characters per chunk
overlap = 200          # Overlap between chunks

# For technical documentation
chunk_size = 1500      # Larger chunks for complex topics
overlap = 300          # More overlap for context preservation

# For reference materials
chunk_size = 800       # Smaller chunks for quick lookup
overlap = 100          # Less overlap for distinct facts
```

## Memory Performance Optimization

### Memory Usage by Configuration

**Minimal Configuration**:
- Short-term: 20 entries (~10KB)
- Long-term: Disabled
- Knowledge base: Disabled
- RAM usage: ~50MB

**Standard Configuration**:
- Short-term: 50 entries (~25KB) 
- Long-term: 100 summaries (~500KB)
- Knowledge base: 1000 chunks (~10MB)
- RAM usage: ~200MB

**Full Features**:
- Short-term: 100 entries (~50KB)
- Long-term: 500 summaries (~2MB)
- Knowledge base: 5000+ chunks (~50MB)
- RAM usage: ~500MB

### Performance Tips

**For Better Response Speed**:
1. Use smaller knowledge bases (limit to essential topics)
2. Reduce embedding search results (`k=3` instead of `k=5`)
3. Set lower `max_context_entries` in configuration
4. Use `/preset minimal` for basic operations

**For Better Memory Recall**:
1. Enable automatic summarization
2. Use comprehensive knowledge bases
3. Increase search result limits
4. Use `/preset full_features`

**Balancing Act**:
```python
# Configuration example for balanced performance
max_context_entries = 30      # Moderate recent context
search_results_limit = 4      # Good relevance without overload
auto_summarize_threshold = 40 # Regular summarization
enable_base_memory = True     # Keep knowledge base active
```

## Memory System Troubleshooting

### Common Issues and Solutions

**"Memory search is slow"**:
- Reduce knowledge base size
- Lower search result limits
- Check if Ollama embedding model is running efficiently
- Use `/preset standard` instead of `/preset full_features`

**"Assistant doesn't remember past conversations"**:
- Check if `/toggle_memory` is enabled
- Verify `embeddings.json` contains summaries
- Try `/summarize` to create summaries manually
- Use `/search_memory <topic>` to test search functionality

**"Knowledge base responses seem irrelevant"**:
- Check embedding quality with `/debug_search <query>`
- Verify source documents are well-formatted
- Re-embed documents with better chunking
- Use more specific queries

**"Memory files are getting too large"**:
- Run `/summarize` to compress old conversations
- Archive old embedding files manually
- Use `/clear_memory` to reset (keeps knowledge base)
- Configure smaller `max_context_entries`

### Memory File Recovery

**If memory.json is corrupted**:
```bash
# Backup and reset
cp personality/memory/memory.json personality/memory/memory_backup.json
echo "[]" > personality/memory/memory.

**If embeddings.json is corrupted**:
```bash
# Reset embeddings (will lose conversation summaries)
echo "[]" > personality/memory/embeddings.json
# Use /summarize to rebuild from recent conversations
```

**If knowledge base is missing**:
```bash
# Re-run document embedding
python BASE/memory_methods/embed_document.py
# Or restore from backup
cp backup/base_memory/* personality/memory_base/base_memory/
```

## Advanced Memory Features

### Memory Export/Import

**Export personal memory**:
```python
memory_manager.export_memory("backup/my_conversations_2025.json")
```

**Import from another system**:
```python
memory_manager.import_memory("backup/previous_conversations.json")
```

### Memory Analytics

**Detailed memory statistics**:
- Conversation entry count and date range
- Summary embedding distribution by topic
- Knowledge base chunk breakdown by category
- Memory file sizes and growth trends
- Search frequency by category

**Memory health monitoring**:
- Embedding quality scores
- Search result relevance tracking
- Memory access patterns
- Performance metrics over time

This sophisticated memory system enables the AI assistant to provide contextually aware responses while maintaining excellent performance. The multi-layered approach ensures that recent conversations remain immediately accessible while historical knowledge is efficiently searchable through semantic similarity.

# Android Mobile Version Setup

## Overview

The AI assistant includes a specialized Android version designed to run on mobile devices using Termux, a Linux terminal emulator for Android. This mobile version provides a streamlined experience with text and voice interaction capabilities, making your AI assistant portable and accessible anywhere.

## Mobile Version Features

### Core Capabilities
- **Text Chat**: Full conversation capabilities with memory retention
- **Voice Input**: Android speech-to-text integration via `termux-speech-to-text`
- **Voice Output**: Text-to-speech responses using `termux-tts-speak`
- **Web Search**: Internet search functionality using DuckDuckGo
- **Memory System**: Personal conversation memory with automatic summarization
- **Intelligent Search**: Automatic determination of when web searches would be helpful

### Mobile-Optimized Features
- **Lightweight Operation**: Uses smaller AI models optimized for mobile hardware
- **Battery Efficient**: Streamlined processing to preserve battery life
- **Touch-Friendly Interface**: Simple command-line interface optimized for mobile keyboards
- **Background Operation**: Can run in Termux background sessions
- **Offline Capable**: Core functionality works without internet (search features require connection)

## Installation Requirements

### Prerequisites
1. **Android Device**: Android 7.0 (API 24) or newer recommended
2. **Storage**: At least 4GB free space for Termux, Python, and AI models
3. **RAM**: Minimum 4GB RAM, 6GB+ recommended for better performance
4. **Termux**: Install from F-Droid (NOT Google Play Store)
5. **Termux:API**: Required for speech and TTS functionality

### Critical Installation Notes
- **F-Droid Source**: Termux from Google Play Store is outdated and incompatible. Use F-Droid version only
- **Permissions**: Microphone and storage permissions must be granted manually
- **Keyboard**: Consider installing Hacker's Keyboard from F-Droid for better terminal experience

## Step-by-Step Mobile Installation

### Step 1: Install Termux Environment
1. Download F-Droid from [f-droid.org](https://f-droid.org)
2. Install F-Droid APK and open it
3. Search for and install:
   - **Termux** (terminal emulator)
   - **Termux:API** (system integration)
   - **Hacker's Keyboard** (optional, better terminal keyboard)

### Step 2: Configure Android Permissions
1. Go to Android **Settings** → **Apps** → **Termux**
2. Navigate to **Permissions** and enable:
   - **Microphone** (for voice input)
   - **Storage** (for file access)
3. For **Termux:API**, ensure all permissions are granted

### Step 3: Set Up Termux Environment
Open Termux and run these commands:

```bash
# Update package lists
pkg update && pkg upgrade

# Install required packages
pkg install python nodejs-lts git termux-api

# Install Python packages
pip install requests beautifulsoup4 ollama

# Create project directory
mkdir -p ~/ai-assistant
cd ~/ai-assistant
```

### Step 4: Install Ollama on Android
```bash
# Download and install Ollama for Android
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Download lightweight models for mobile
ollama pull gemma2:2b
ollama pull llama3.1:8b
```

### Step 5: Set Up Mobile Assistant Files
```bash
# Create project structure
mkdir -p personality/memory
mkdir -p BASE

# Create the main bot file (copy bot_mob.py content)
nano bot_mob.py

# Create system prompt file
mkdir -p personality
nano personality/SYS_MSG.py

# Create bot configuration
nano personality/bot_info.py
```

## Mobile-Specific Configuration

### Model Selection
The mobile version uses lighter models for better performance:
- **Default**: `gemma2:2b` (2GB model, fastest)
- **Alternative**: `llama3.1:8b` (8GB model, better quality)
- **Embedding**: Uses Ollama's built-in embedding for memory

### Memory Configuration
Mobile memory settings are optimized for limited resources:
```python
# In the mobile version
max_entries = 20           # Fewer recent entries
search_results_limit = 3   # Fewer search results
auto_summarize_threshold = 15  # More frequent summarization
```

### Voice Configuration
The mobile version integrates with Android's native speech services:
- **Speech-to-Text**: Uses `termux-speech-to-text` command
- **Text-to-Speech**: Uses `termux-tts-speak` command
- **Language Support**: Supports multiple languages based on Android system settings

## Usage Instructions

### Starting the Mobile Assistant
```bash
cd ~/ai-assistant
python bot_mob.py
```

### Interface Modes

#### Text Mode
- Type messages normally
- Use standard conversation commands
- Memory and search work automatically
- Type `exit` to quit

#### Voice Mode
- Press Enter to start voice input
- Speak your message clearly
- Assistant responds with both text and speech
- Say "exit" to quit voice mode

### Mobile-Specific Commands
While the mobile version uses the same basic commands, some are optimized:
- Voice input automatically triggered by pressing Enter in voice mode
- Search results are automatically summarized for mobile viewing
- Memory searches return fewer, more relevant results

## Intelligent Features

### Automatic Search Detection
The mobile assistant includes smart search evaluation:
- **Speech Summarization**: Cleans up speech-to-text errors and combines fragmented input
- **Search Need Detection**: Automatically determines when web search would be helpful
- **Query Extraction**: Generates optimal search queries from conversational input
- **Result Summarization**: Condenses search results into key points for mobile viewing

### Example Automatic Behaviors
- "I wonder what the weather will be like tomorrow" → Automatically searches "weather forecast tomorrow"
- "I'm not sure who won the game last night" → Searches "game results last night"
- "I had a great day at work today" → No search needed, normal conversation

## Performance Optimization

### For Lower-End Devices (2-4GB RAM)
```bash
# Use smallest model
ollama pull gemma2:2b

# Limit memory usage in bot configuration
max_entries = 10
search_results_limit = 2
```

### For Higher-End Devices (6GB+ RAM)
```bash
# Use better model
ollama pull llama3.1:8b

# Allow more memory usage
max_entries = 30
search_results_limit = 5
```

### Battery Optimization
- Run Ollama only when needed: `ollama serve` when starting, `pkill ollama` when done
- Use Termux wake locks: `termux-wake-lock` to prevent sleeping during long conversations
- Close unused Termux sessions: `exit` from unused terminals

## Troubleshooting Mobile Issues

### "Speech-to-text not working"
1. Verify Termux:API is installed from F-Droid
2. Check microphone permissions in Android settings
3. Test with: `termux-speech-to-text`
4. Ensure device has Google Speech Services or similar installed

### "Text-to-speech silent"
1. Test manually: `termux-tts-speak "hello"`
2. Check if Android TTS engine is configured
3. Go to Android Settings → Accessibility → Text-to-speech
4. Install Google Text-to-Speech if missing

### "Ollama connection failed"
1. Check if Ollama is running: `ps aux | grep ollama`
2. Start Ollama manually: `ollama serve &`
3. Test connection: `ollama list`
4. Try reinstalling: `curl -fsSL https://ollama.ai/install.sh | sh`

### "Python module not found"
1. Ensure you're in the correct directory: `cd ~/ai-assistant`
2. Reinstall packages: `pip install requests beautifulsoup4 ollama`
3. Check Python path: `which python`

### "Model not found errors"
1. List available models: `ollama list`
2. Pull required model: `ollama pull gemma2:2b`
3. Wait for download to complete (can take 10-30 minutes on mobile)

### "Memory or search errors"
1. Check file permissions: `ls -la personality/memory/`
2. Create memory directory: `mkdir -p personality/memory`
3. Reset memory if corrupted: `echo "[]" > personality/memory/memory.json`

## Mobile-Specific Limitations

### Hardware Constraints
- **Processing Speed**: Responses may be slower than desktop versions
- **Model Size**: Limited to smaller AI models due to memory constraints
- **Battery Usage**: Extended use will drain battery faster
- **Heat Generation**: Intensive AI processing may cause device warming

### Feature Limitations
- **No Vision Processing**: Camera/screen analysis not supported on mobile version
- **No Minecraft Integration**: Gaming features require full desktop setup
- **No Avatar Animation**: Warudo integration not available on mobile
- **Limited Multitasking**: Best used as primary foreground app

### Network Considerations
- **Data Usage**: Web searches and model downloads use mobile data
- **Offline Mode**: Basic conversation works offline, but search features require internet
- **Latency**: Mobile networks may cause slower web search responses

## Cross-Device Memory Synchronization

### Overview

One of the most powerful features of this AI assistant is the ability to maintain persistent memory across multiple devices using Git repositories. This allows you to seamlessly continue conversations between your desktop computer, Android device, and any other system where you run the assistant, with full access to your conversation history and learned knowledge.

### How Cross-Device Memory Works

The memory synchronization system leverages Git's distributed version control to keep memory files synchronized:

- **Personal Memory**: Your conversation history (`memory.json`) syncs across devices
- **Long-term Summaries**: Conversation summaries (`embeddings.json`) remain accessible everywhere
- **Custom Knowledge**: Any knowledge bases you create travel with you
- **Configuration Settings**: Your personalized assistant settings sync automatically

### Setting Up Memory Synchronization

#### Step 1: Create a Private Git Repository

Create a private repository on your preferred Git service:

**GitHub (Recommended)**:
1. Go to [github.com](https://github.com) and create a new repository
2. Name it something like `my-ai-assistant` or `personal-ai-memory`
3. **IMPORTANT**: Set the repository to **Private** to protect your conversation data
4. Initialize with a README if desired

**Alternative Services**:
- GitLab, Bitbucket, or self-hosted Git servers work equally well
- Ensure the repository is private to protect personal conversations

#### Step 2: Initialize Your Primary Device

On your main device (desktop or mobile), set up Git tracking:

```bash
# Navigate to your AI assistant directory
cd /path/to/your/OllamaAI  # Desktop
cd ~/ai-assistant          # Android/Termux

# Initialize Git repository
git init

# Add your remote repository
git remote add origin https://github.com/yourusername/my-ai-assistant.git

# Create .gitignore file to exclude temporary files
cat > .gitignore << EOF
# Python cache
__pycache__/
*.pyc
*.pyo

# Virtual environment
venv/
env/

# Temporary files
*.tmp
*.log

# OS files
.DS_Store
Thumbs.db

# Large model files (optional - these are recreated by Ollama)
models/
*.bin
EOF

# Add all files including memory
git add .
git commit -m "Initial setup of AI assistant with memory"
git push -u origin main
```

#### Step 3: Setting Up Additional Devices

On each new device where you want to run the assistant:

```bash
# Clone the repository
git clone https://github.com/yourusername/my-ai-assistant.git
cd my-ai-assistant

# Install dependencies as normal
pip install -r requirements.txt
# ... continue with normal setup
```

### Daily Workflow for Memory Sync

#### Before Using the Assistant

Always pull the latest memory before starting a conversation:

```bash
# Navigate to your AI assistant directory
cd /path/to/your/ai-assistant

# Pull latest memory from other devices
git pull origin main

# Now start your assistant
python BASE/bot.py              # Desktop
python bot_mob.py               # Android
```

#### After Using the Assistant

Push your memory updates so other devices can access them:

```bash
# After finishing your conversation session
git add personality/memory/
git commit -m "Updated memory: $(date)"
git push origin main
```

### Automated Memory Sync Scripts

#### Desktop Automation (Windows/Mac/Linux)

Create a startup script that automatically syncs memory:

**For Windows** (`sync_and_start.bat`):
```batch
@echo off
cd /d "C:\path\to\your\OllamaAI"
echo Syncing memory from other devices...
git pull origin main
echo Starting AI Assistant...
python BASE\bot.py
echo Saving memory updates...
git add personality\memory\
git commit -m "Memory update from desktop: %date% %time%"
git push origin main
pause
```

**For Mac/Linux** (`sync_and_start.sh`):
```bash
#!/bin/bash
cd /path/to/your/OllamaAI
echo "Syncing memory from other devices..."
git pull origin main
echo "Starting AI Assistant..."
python BASE/bot.py
echo "Saving memory updates..."
git add personality/memory/
git commit -m "Memory update from desktop: $(date)"
git push origin main
```

#### Android Automation (Termux)

Create a sync script for Android (`sync_memory.sh`):
```bash
#!/bin/bash
cd ~/ai-assistant
echo "Syncing memory..."
git pull origin main
echo "Memory sync complete. Starting assistant..."
python bot_mob.py
echo "Saving conversation updates..."
git add personality/memory/
git commit -m "Memory update from Android: $(date)"
git push origin main
echo "Memory saved to repository."
```

Make it executable:
```bash
chmod +x sync_memory.sh
./sync_memory.sh
```

### Advanced Memory Management

#### Selective Memory Sync

You can choose which memory components to sync:

```bash
# Sync only personal conversations
git add personality/memory/memory.json
git add personality/memory/embeddings.json

# Sync only knowledge bases
git add personality/memory_base/

# Sync configuration changes
git add personality/config.json
git add personality/bot_info.py
```

#### Branch-Based Memory Management

For advanced users, create different memory branches for different contexts:

```bash
# Create a work-focused memory branch
git checkout -b work-assistant
# Use assistant for work-related conversations

# Switch to personal conversations
git checkout -b personal-assistant
# Use assistant for personal topics

# Merge insights between branches when desired
git checkout main
git merge work-assistant
git merge personal-assistant
```

### Memory Conflict Resolution

#### Handling Merge Conflicts

When memory files conflict between devices:

```bash
# If you encounter merge conflicts
git pull origin main
# Git will show conflict markers in memory files

# Edit conflicted files manually, or
# Choose one version completely:
git checkout --theirs personality/memory/memory.json  # Use remote version
git checkout --ours personality/memory/memory.json    # Use local version

# Complete the merge
git add personality/memory/
git commit -m "Resolved memory conflict"
git push origin main
```

#### Preventing Conflicts

**Best Practices**:
1. Always pull before starting conversations
2. Push immediately after conversations
3. Don't run the assistant simultaneously on multiple devices
4. Use meaningful commit messages with device/date information

**Automatic Conflict Prevention**:
```bash
# Add this to your sync script to prevent conflicts
git stash                    # Save local changes
git pull origin main         # Get remote changes
git stash pop               # Restore local changes
# Handle any conflicts manually
```

### Security and Privacy Considerations

#### Repository Security

**Essential Security Measures**:
- **Always use private repositories** - conversation data is personal
- **Enable two-factor authentication** on your Git service account
- **Use SSH keys** instead of passwords for authentication
- **Review repository permissions** regularly

#### Data Protection

**What Gets Synced**:
- Conversation memories (may contain personal information)
- Configuration settings (assistant name, preferences)
- Knowledge bases (usually safe to share)
- System prompts (may contain personal customizations)

**What Should NOT Be Synced**:
- API keys or authentication tokens (use `.env` files and `.gitignore`)
- Large model files (rebuilt on each device via Ollama)
- Temporary cache files
- System-specific configurations

#### Sensitive Data Management

```bash
# Create environment-specific config files
cp .env .env.example           # Create template
echo ".env" >> .gitignore      # Never sync actual API keys

# For sensitive memory, consider encryption
gpg -c personality/memory/memory.json  # Encrypt before commit
git add personality/memory/memory.json.gpg
```

### Troubleshooting Sync Issues

#### Common Problems and Solutions

**"Repository not found" errors**:
- Verify repository URL: `git remote -v`
- Check authentication: `git config --global user.name` and `user.email`
- Ensure repository is accessible from current device

**Memory file corruption**:
```bash
# Reset corrupted memory files
git checkout HEAD -- personality/memory/memory.json
# Or restore from a previous commit
git log --oneline personality/memory/memory.json
git checkout <commit-hash> -- personality/memory/memory.json
```

**Large repository size**:
```bash
# Check repository size
git count-objects -vH

# Clean up history if needed (WARNING: destructive)
git filter-branch --tree-filter 'rm -f large-file.bin' HEAD
```

**Sync failures**:
```bash
# Force push (use carefully)
git push --force-with-lease origin main

# Reset to remote state (loses local changes)
git reset --hard origin/main
```

### Multi-User Memory Sharing

#### Family or Team Assistant

For shared AI assistants (family use, team projects):

```bash
# Create shared repository with multiple contributors
git remote add shared-memory https://github.com/family/shared-assistant.git

# Pull from shared memory
git pull shared-memory main

# Push to shared memory (with approval workflow)
git push shared-memory feature/new-knowledge
# Create pull request for review
```

#### Privacy-Preserving Shared Knowledge

```bash
# Share only knowledge bases, not personal conversations
git add personality/memory_base/
git commit -m "Shared knowledge update"
git push shared-knowledge main

# Keep personal memory separate
git add personality/memory/
git commit -m "Personal conversation update" 
git push personal-memory main
```

This cross-device memory synchronization transforms your AI assistant into a truly personal, persistent companion that grows smarter and more helpful regardless of which device you're using. The system ensures your conversations, learned knowledge, and customizations are always available, creating a seamless AI experience across your entire digital ecosystem.