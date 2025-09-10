const express = require("express");
const cors = require("cors");
const { createBot, initializeBot } = require('./bot');
const { parseAction, handleAction } = require('./bot-actions');
const { getVisionData } = require('./world-info');

// Environment variables
const LISTEN_PORT = parseInt(process.env.LISTEN_PORT || "3001", 10);
const API_KEY = process.env.API_KEY || null;

// Create Express app
const app = express();
app.use(express.json());
app.use(cors()); // Allow cross-origin requests

// Optional authentication middleware
function requireAuth(req, res, next) {
  if (!API_KEY) return next();
  const key = req.header("X-API-Key");
  if (!key || key !== API_KEY) {
    return res.status(401).json({ 
      error: "Unauthorized", 
      message: "Valid API key required" 
    });
  }
  next();
}

// Global bot instance with proper error handling
let bot = null;
let botInitialized = false;
let lastError = null;

// Initialize bot with retry logic
async function initializeBotWithRetry(maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`🎮 Bot initialization attempt ${attempt}/${maxRetries}`);
      bot = createBot();
      initializeBot(bot);
      
      // Wait for bot to be ready
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("Bot initialization timeout"));
        }, 30000);
        
        bot.once('spawn', () => {
          setTimeout(() => {
            clearTimeout(timeout);
            botInitialized = true;
            lastError = null;
            console.log("✅ Bot initialized successfully");
            resolve();
          }, 2000); // Give plugins time to load
        });
        
        bot.once('error', (err) => {
          clearTimeout(timeout);
          lastError = err;
          reject(err);
        });
      });
      
      break; // Success, exit retry loop
      
    } catch (err) {
      console.error(`❌ Bot initialization attempt ${attempt} failed:`, err.message);
      lastError = err;
      botInitialized = false;
      
      if (bot) {
        try {
          bot.end();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      bot = null;
      
      if (attempt < maxRetries) {
        console.log(`⏳ Retrying in 5 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
  }
  
  if (!botInitialized) {
    console.error("💥 Failed to initialize bot after all attempts");
  }
}

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({
    status: "online",
    botConnected: !!bot,
    botSpawned: !!(bot && bot.entity),
    botReady: !!(bot && bot.botReady),
    lastError: lastError ? lastError.message : null,
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Vision endpoint - provides detailed environmental information
app.get("/api/vision",  (req, res) => {
  try {
    if (!bot) {
      return res.status(503).json({
        status: "error",
        error: "Bot not connected",
        lastError: lastError ? lastError.message : null
      });
    }
    
    if (!bot.entity) {
      return res.status(503).json({
        status: "error",
        error: "Bot not spawned in world yet"
      });
    }
    
    const visionData = getVisionData(bot);
    res.json({
      status: "success",
      vision: visionData
    });
    console.log("SENT VISION /API/VISION")
    
  } catch (err) {
    console.error("[Vision] Error:", err);
    return res.status(500).json({
      status: "error",
      error: "Failed to get bot vision: " + (err.message || String(err)),
      stack: process.env.NODE_ENV === "development" ? err.stack : undefined,
    });
  }
});

// Action endpoint - handles natural language commands (primary)
app.post("/api/action",  async (req, res) => {
  await handleAction(req, res, bot, parseAction);
});

// Legacy action endpoint (compatibility)
app.post("/api/act",  async (req, res) => {
  await handleAction(req, res, bot, parseAction);
});

// Status endpoint - provides comprehensive bot status
app.get("/api/status",  (req, res) => {
  const inv = bot && bot.inventory
    ? bot.inventory.items().map((i) => ({ 
        id: i.type, 
        count: i.count, 
        name: i.name,
        displayName: i.displayName
      }))
    : [];
    
  const pos = bot && bot.entity ? {
    x: Math.round(bot.entity.position.x * 100) / 100,
    y: Math.round(bot.entity.position.y * 100) / 100,
    z: Math.round(bot.entity.position.z * 100) / 100
  } : null;

  res.json({
    // Connection status
    connected: !!bot,
    spawned: !!bot?.entity,
    ready: bot?.botReady || false,
    initialized: botInitialized,
    
    // Bot state
    position: pos,
    health: bot?.health || null,
    food: bot?.food || null,
    experience: bot?.experience || null,
    gameMode: bot?.game?.gameMode || null,
    dimension: bot?.game?.dimension || null,
    
    // Inventory
    inventory: inv,
    inventoryCount: inv.length,
    
    // Technical info
    version: bot?.version || null,
    pluginsLoaded: bot?.pluginsLoaded || false,
    mcDataAvailable: !!(bot?.mcData),
    mcDataVersion: bot?.mcData?.version || null,
    
    // Server info
    serverInfo: {
      host: process.env.MC_HOST || "localhost",
      port: parseInt(process.env.MC_PORT || "63968", 10),
      botName: process.env.BOT_NAME || "Anna",
    },
    
    // Runtime info
    lastError: lastError ? lastError.message : null,
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("[Server] Unhandled error:", err);
  res.status(500).json({
    status: "error",
    error: "Internal server error",
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    status: "error",
    error: "Endpoint not found",
    available_endpoints: [
      "GET /api/health",
      "GET /api/vision", 
      "POST /api/action",
      "POST /api/act",
      "GET /api/status"
    ]
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 SIGTERM received, shutting down gracefully');
  if (bot) {
    bot.end();
  }
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🛑 SIGINT received, shutting down gracefully');
  if (bot) {
    bot.end();
  }
  process.exit(0);
});

// Start server and initialize bot
async function start() {
  // Start HTTP server first
  const server = app.listen(LISTEN_PORT, "127.0.0.1", () => {
    console.log(
      `🌐 Ollama-MC API listening on http://127.0.0.1:${LISTEN_PORT}` +
      (API_KEY ? " (API key required)" : " (no API key configured)")
    );
  });
  
  // Then initialize bot
  await initializeBotWithRetry();
  
  return { app, bot, server };
}

// Export for testing
module.exports = { app, bot: () => bot, start };

// Start if run directly
if (require.main === module) {
  start().catch(err => {
    console.error("💥 Failed to start server:", err);
    process.exit(1);
  });
}