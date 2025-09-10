# Minecraft Bot API

A modular Minecraft bot with REST API interface built using Mineflayer. The bot can perform various actions in Minecraft worlds through natural language commands and provides detailed environmental information.

## Project Structure

```
├── server.js           # Main Express server and API endpoints
├── bot.js              # Bot creation, initialization, and plugin management
├── bot-actions.js      # Action handlers and natural language parser
├── world-info.js       # World vision and environmental data collection
├── package.json        # Dependencies and project configuration
└── README.md           # This file
```

## Features

- **Modular Architecture**: Clean separation of concerns across multiple files
- **Natural Language Processing**: Simple parser that converts text commands to bot actions
- **Environmental Awareness**: Detailed vision system providing information about surroundings
- **Pathfinding**: Smart movement using mineflayer-pathfinder
- **Block Collection**: Automated resource gathering
- **Player Following**: Bot can follow nearby players
- **REST API**: Clean HTTP interface for all bot interactions

## Environment Variables

Create a `.env` file or set these environment variables:

```env
MC_HOST=localhost                    # Minecraft server host
MC_PORT=25565                       # Minecraft server port (default shown, original uses 63968)
BOT_NAME=Anna                       # Bot username
LISTEN_PORT=3001                    # API server port
MC_PROTOCOL=1.16                    # Minecraft version for data loading
API_KEY=optional_api_key            # Optional API authentication
FORCE_MC_VERSION=1.16.5            # Force specific MC version (optional)
NODE_ENV=development               # Environment mode
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up your environment variables
4. Start the bot:
   ```bash
   npm start
   ```

For development with auto-reload:
```bash
npm run dev
```

## API Endpoints

### GET /api/status
Returns bot status and diagnostic information including:
- Connection status
- Position and health
- Inventory summary
- Plugin status
- Server information

### GET /api/vision
Returns detailed environmental information including:
- Bot position and rotation
- Nearby blocks and entities
- Time and weather conditions
- Inventory details
- Movement capabilities
- Biome information

### POST /api/act
Send natural language commands to the bot.

**Request body:**
```json
{
  "text": "gather wood"
}
```

**Supported commands:**
- `"gather wood"` - Find and chop trees
- `"gather stone"` - Mine stone blocks
- `"craft planks"` - Craft planks from logs in inventory
- `"go to 100 64 200"` - Move to specific coordinates
- `"go to player"` - Move near the nearest player
- `"follow player"` - Start following the nearest player
- `"place block"` - Place a block in front of the bot
- `"stop"` - Stop all current activities

## Module Details

### server.js
Main Express application that:
- Sets up API endpoints
- Handles HTTP requests and responses
- Manages bot instance
- Provides status and diagnostic information

### bot.js
Bot management module that:
- Creates and configures the mineflayer bot
- Initializes minecraft-data with proper version handling
- Loads plugins (pathfinder, collectblock)
- Handles bot events and state management
- Provides utility functions for accessing bot data

### bot-actions.js
Action handling module that:
- Parses natural language commands into structured actions
- Implements all bot behaviors (movement, gathering, crafting, etc.)
- Manages pathfinding and goal-setting
- Handles error conditions and timeouts
- Provides utility functions for bot control

### world-info.js
Environmental awareness module that:
- Scans the environment for blocks and entities
- Provides detailed vision information
- Analyzes surroundings and capabilities
- Handles biome, weather, and time information
- Optimizes data collection for performance

## Development

The modular structure makes it easy to:

- **Add new actions**: Extend the parser in `bot-actions.js` and add corresponding handlers
- **Enhance vision**: Modify `world-info.js` to collect additional environmental data
- **Add API endpoints**: Extend `server.js` with new routes
- **Improve bot behavior**: Modify initialization and plugin loading in `bot.js`

## Error Handling

Each module includes comprehensive error handling:
- Graceful degradation when plugins fail to load
- Timeout protection for long-running operations
- Detailed error reporting in API responses
- Fallback behaviors for missing data

## Performance Considerations

- Block scanning is limited to prevent performance issues
- Entity processing includes distance filtering
- Environmental scans are optimized with early termination
- Memory usage is managed through array size limits

## Troubleshooting

1. **Bot won't connect**: Check MC_HOST and MC_PORT environment variables
2. **Plugins not loading**: Verify minecraft-data version compatibility
3. **Actions failing**: Ensure bot has spawned and plugins are loaded
4. **Performance issues**: Reduce scan distances in world-info.js

## License

MIT License - see package.json for details