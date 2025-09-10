const mineflayer = require("mineflayer");
const pathfinderModule = require("mineflayer-pathfinder");
const collectBlockPlugin = require("mineflayer-collectblock").plugin;

// Environment variables
const SERVER_HOST = process.env.MC_HOST || "localhost";
const SERVER_PORT = parseInt(process.env.MC_PORT || "58179", 10);
const BOT_NAME = process.env.BOT_NAME || "Anna";
const MC_DATA_VERSION = process.env.MC_PROTOCOL || "1.16";

// Improved minecraft-data loading with better error handling
let minecraftDataFunc = null;
let minecraftDataExplicit = null;

try {
  minecraftDataFunc = require("minecraft-data");
  console.log("✅ minecraft-data module loaded successfully");

  try {
    minecraftDataExplicit = minecraftDataFunc(MC_DATA_VERSION);
    console.log(`✅ Pre-loaded minecraft-data for version ${MC_DATA_VERSION}`);
  } catch (err) {
    console.warn(
      `⚠️ Could not pre-load minecraft-data for ${MC_DATA_VERSION}:`,
      err.message
    );
    minecraftDataExplicit = null;
  }
} catch (err) {
  console.error("❌ Failed to load minecraft-data module:", err.message);
  minecraftDataFunc = null;
  minecraftDataExplicit = null;
}

// Better mcData initialization with proper attachment
function initializeMcData(bot) {
  if (!minecraftDataFunc) {
    console.warn("⚠️ minecraft-data function not available");
    return null;
  }

  let data = null;

  // Try bot version first
  if (bot.version) {
    try {
      data = minecraftDataFunc(bot.version);
      console.log(`✅ Loaded minecraft-data for bot version: ${bot.version}`);
    } catch (err) {
      console.warn(
        `⚠️ Failed to load minecraft-data for bot version ${bot.version}:`,
        err.message
      );
    }
  }

  // Fall back to explicit version if bot version failed
  if (!data && minecraftDataExplicit) {
    try {
      data = minecraftDataExplicit;
      console.log(`✅ Using pre-loaded minecraft-data version: ${MC_DATA_VERSION}`);
    } catch (err) {
      console.warn("⚠️ Failed to use pre-loaded minecraft-data:", err.message);
    }
  }

  // Properly attach mcData to bot object
  if (data) {
    try {
      bot.mcData = data;
      console.log(`✅ Attached mcData to bot object`);
      console.log(`  - Version: ${data.version || 'unknown'}`);
      console.log(
        `  - Blocks: ${data.blocks ? Object.keys(data.blocks).length : 0}`
      );
      console.log(
        `  - Items: ${data.items ? Object.keys(data.items).length : 0}`
      );
      console.log(`  - blocksByName available: ${!!data.blocksByName}`);
      console.log(`  - itemsByName available: ${!!data.itemsByName}`);
    } catch (err) {
      console.error("❌ Failed to attach mcData to bot:", err.message);
    }
  }

  return data;
}

// Load plugins with proper error handling and mcData validation
function loadPlugins(bot, mcData) {
  let loadedCount = 0;

  // Validate mcData before loading plugins
  if (!mcData || !mcData.blocksByName) {
    console.error(
      "❌ Cannot load plugins: mcData or blocksByName not available"
    );
    return false;
  }

  // Load pathfinder with proper validation
  try {
    if (pathfinderModule && typeof pathfinderModule.pathfinder === "function") {
      bot.loadPlugin(pathfinderModule.pathfinder);
      console.log("✅ Pathfinder plugin loaded successfully");
      loadedCount++;
    } else if (typeof pathfinderModule === "function") {
      bot.loadPlugin(pathfinderModule);
      console.log("✅ Pathfinder plugin (direct) loaded successfully");
      loadedCount++;
    } else if (pathfinderModule && pathfinderModule.Movements && pathfinderModule.goals) {
      // Alternative loading method for some pathfinder versions
      bot.pathfinder = pathfinderModule;
      console.log("✅ Pathfinder plugin (manual) loaded successfully");
      loadedCount++;
    } else {
      console.warn("⚠️ Pathfinder plugin not found or invalid format");
    }
  } catch (err) {
    console.error("❌ Failed to load pathfinder plugin:", err.message);
  }

  // Load collectblock
  try {
    if (typeof collectBlockPlugin === "function") {
      bot.loadPlugin(collectBlockPlugin);
      console.log("✅ Collectblock plugin loaded successfully");
      loadedCount++;
    } else {
      console.warn("⚠️ Collectblock plugin not found or invalid format");
    }
  } catch (err) {
    console.error("❌ Failed to load collectblock plugin:", err.message);
  }

  const success = loadedCount > 0;
  console.log(
    `${success ? "✅" : "❌"} Loaded ${loadedCount} plugins successfully`
  );
  return success;
}

// Create bot function
function createBot() {
  const botOptions = {
    host: SERVER_HOST,
    port: SERVER_PORT,
    username: BOT_NAME,
  };
  
  // Version override options
  if (process.env.FORCE_MC_VERSION) {
    botOptions.version = process.env.FORCE_MC_VERSION;
    console.log(`🎮 Forcing Minecraft version: ${process.env.FORCE_MC_VERSION}`);
  }
  if (process.env.MC_PROTOCOL_FORCE) {
    botOptions.version = process.env.MC_PROTOCOL_FORCE;
    console.log(`🎮 Forcing protocol version: ${process.env.MC_PROTOCOL_FORCE}`);
  }

  console.log(`🎮 Creating bot with options:`, {
    host: botOptions.host,
    port: botOptions.port,
    username: botOptions.username,
    version: botOptions.version || 'auto-detect'
  });

  const bot = mineflayer.createBot(botOptions);
  
  // Initialize state properties
  bot.pluginsLoaded = false;
  bot.botReady = false;
  bot.mcData = null;
  
  return bot;
}

// Initialize bot function
function initializeBot(bot) {
  // Bot initialization logic
  bot.once("spawn", () => {
    console.log("🚀 Bot spawned, initializing mcData and plugins...");

    // Initialize mcData with proper error handling
    const mcData = initializeMcData(bot);

    // Add a short delay to ensure bot.version is fully synced
    setTimeout(() => {
      if (mcData && mcData.blocksByName) {
        console.log("✅ mcData initialized successfully with blocksByName");

        // Load plugins after mcData is confirmed working
        try {
          bot.pluginsLoaded = loadPlugins(bot, mcData);
          if (bot.pluginsLoaded) {
            console.log("🎉 Bot is ready with all systems operational!");
            bot.botReady = true;
          } else {
            console.warn("⚠️ Bot is ready but some plugins failed to load");
            bot.botReady = true; // Still mark as ready for basic functionality
          }
        } catch (err) {
          console.error("❌ Error during plugin loading:", err.message);
          bot.pluginsLoaded = false;
          bot.botReady = true; // Mark ready for basic functionality
        }
      } else {
        console.error(
          "❌ Failed to initialize mcData properly - limited functionality"
        );
        console.warn("    - mcData availability:", !!mcData);
        if (mcData) {
          console.warn("    - blocksByName availability:", !!mcData.blocksByName);
          console.warn("    - itemsByName availability:", !!mcData.itemsByName);
        }
        bot.pluginsLoaded = false;
        bot.botReady = true; // Allow basic functionality
      }
    }, 1000); // 1 second delay
  });

  // Bot event handlers with better logging
  bot.on("login", () => {
    console.log(`✅ Bot logged in as ${BOT_NAME}`);
    console.log(`🌍 Server: ${SERVER_HOST}:${SERVER_PORT}`);
    if (bot.version) {
      console.log(`🎮 Minecraft version: ${bot.version}`);
    }
  });
  
  bot.on("spawn", () => {
    console.log("🌍 Bot spawned in the world");
    if (bot.entity && bot.entity.position) {
      console.log(`📍 Position: ${bot.entity.position.x}, ${bot.entity.position.y}, ${bot.entity.position.z}`);
    }
  });
  
  bot.on("kicked", (reason) => {
    console.warn("⛔ Bot kicked:", reason);
    bot.botReady = false;
    bot.pluginsLoaded = false;
    bot.mcData = null;
  });
  
  bot.on("error", (err) => {
    console.error("🚨 Bot error:", err && err.stack ? err.stack : err);
  });
  
  bot.on("end", () => {
    console.warn("🔌 Bot disconnected. Restart the service to reconnect.");
    bot.botReady = false;
    bot.pluginsLoaded = false;
    bot.mcData = null;
  });

  // Health and status monitoring
  bot.on("health", () => {
    if (bot.health <= 5) {
      console.warn(`⚠️ Low health: ${bot.health}/20`);
    }
  });

  bot.on("death", () => {
    console.warn("💀 Bot died! Respawning...");
  });
}

// Utility function to get current mcData
function currentMcData(bot) {
  if (bot && bot.mcData) return bot.mcData;
  
  if (minecraftDataFunc && bot && bot.version) {
    try {
      const data = minecraftDataFunc(bot.version);
      // Cache it on the bot for future use
      if (bot) bot.mcData = data;
      return data;
    } catch (e) {
      console.warn("⚠️ Failed to get mcData from bot version:", e.message);
    }
  }
  
  return minecraftDataExplicit || null;
}

// Utility function to check if bot is ready for actions
function isBotReady(bot) {
  return !!(bot && bot.entity && bot.botReady && bot.mcData);
}

module.exports = {
  createBot,
  initializeBot,
  currentMcData,
  isBotReady,
  pathfinderModule
};