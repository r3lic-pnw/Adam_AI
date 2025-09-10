// Filename: actions/action-coordinator.js

// Import all action modules
const { executeGoto, executeFollow, executeApproach, executeStop, executeExplore } = require('./movement-actions');
const { executeGather } = require('./gathering-actions');
const { executeCraft } = require('./crafting-actions');
const { executePlaceBlock, executeBreakBlock } = require('./building-actions');
const { executeAttack } = require('./combat-actions');
const { executeDropItem, executeEquipTool } = require('./inventory-actions');
const { executeLookAround } = require('./observation-actions');

// Action execution timeout constants
const ACTION_TIMEOUT = 30000;
const MOVEMENT_TIMEOUT = 120000;

// Enhanced action execution with better error handling and feedback
async function handleAction(req, res, bot, actionParser) {
  try {
    if (!bot) {
      return res.status(503).json({
        status: "error",
        error: "Bot not connected"
      });
    }
    
    if (!bot.entity) {
      return res.status(503).json({
        status: "error",
        error: "Bot not spawned in world"
      });
    }

    const { text } = req.body;
    if (!text) {
      return res.status(400).json({
        status: "error",
        error: "No text provided"
      });
    }

    console.log(`🎯 Parsing action: "${text}"`);
    const action = actionParser(text);
    
    if (!action) {
      console.log(`❓ No recognizable action found in: "${text}"`);
      return res.json({
        status: "success",
        message: `Acknowledged: "${text}" (no specific action required)`,
        action: "none"
      });
    }

    console.log(`⚡ Executing action:`, action);
    
    // Execute the parsed action with timeout
    const result = await Promise.race([
      executeAction(bot, action),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Action timeout')), 
          action.type === 'goto' ? MOVEMENT_TIMEOUT : ACTION_TIMEOUT)
      )
    ]);

    return res.json({
      status: "success",
      message: result.message,
      action: action.type,
      details: result.details || null
    });

  } catch (error) {
    console.error(`❌ Action execution error:`, error);
    
    // Stop any ongoing pathfinding on error
    if (bot && bot.pathfinder) {
      try {
        bot.pathfinder.setGoal(null);
      } catch (e) {
        // Ignore cleanup errors
      }
    }

    return res.status(500).json({
      status: "error",
      error: error.message || "Action execution failed",
      action: req.body.text
    });
  }
}

// Main action execution function with comprehensive action support
async function executeAction(bot, action) {
  const mcData = bot.mcData;
  if (!mcData) {
    throw new Error("Minecraft data not available");
  }

  switch (action.type) {
    // Movement actions
    case 'goto':
      return await executeGoto(bot, action);
    case 'follow':
      return await executeFollow(bot);
    case 'approach':
      return await executeApproach(bot);
    case 'stop':
      return executeStop(bot);
    case 'explore':
      return await executeExplore(bot);
    
    // Gathering actions
    case 'gather':
      return await executeGather(bot, action.resource);
    
    // Crafting actions
    case 'craft':
      return await executeCraft(bot, action.item);
    
    // Building actions
    case 'place_block':
      return await executePlaceBlock(bot);
    case 'break_block':
      return await executeBreakBlock(bot);
    
    // Combat actions
    case 'attack':
      return await executeAttack(bot);
    
    // Inventory actions
    case 'drop_item':
      return await executeDropItem(bot);
    case 'equip_tool':
      return await executeEquipTool(bot);
    
    // Observation actions
    case 'look_around':
      return executeLookAround(bot);
    
    default:
      throw new Error(`Unknown action type: ${action.type}`);
  }
}

module.exports = {
  handleAction,
  executeAction
};