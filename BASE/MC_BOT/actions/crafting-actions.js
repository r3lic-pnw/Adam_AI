// Filename: actions/crafting-actions.js

async function executeCraft(bot, item) {
  console.log(`🔨 Crafting ${item}`);
  
  const mcData = bot.mcData;
  
  switch (item) {
    case 'planks':
      return await craftPlanks(bot, mcData);
    case 'tools':
      return await craftBasicTools(bot, mcData);
    default:
      throw new Error(`Don't know how to craft: ${item}`);
  }
}

async function craftPlanks(bot, mcData) {
  // Find logs in inventory
  const logTypes = ['oak_log', 'birch_log', 'spruce_log', 'jungle_log', 'acacia_log', 'dark_oak_log'];
  let logItem = null;
  
  for (const logName of logTypes) {
    const logType = mcData.itemsByName[logName];
    if (logType) {
      logItem = bot.inventory.findInventoryItem(logType.id);
      if (logItem) break;
    }
  }
  
  if (!logItem) {
    throw new Error("No logs available for crafting planks");
  }

  // Craft planks (1 log = 4 planks)
  const plankType = mcData.itemsByName[logItem.name.replace('_log', '_planks')];
  if (!plankType) {
    throw new Error("Cannot determine plank type");
  }

  try {
    await bot.craft(plankType, 1);
    return {
      message: `Successfully crafted planks from ${logItem.name}`,
      details: { input: logItem.name, output: plankType.name }
    };
  } catch (err) {
    throw new Error(`Failed to craft planks: ${err.message}`);
  }
}

async function craftBasicTools(bot, mcData) {
  // Try to craft a wooden pickaxe first
  const plankType = mcData.itemsByName.oak_planks || mcData.itemsByName.birch_planks;
  const stickType = mcData.itemsByName.stick;
  const pickaxeType = mcData.itemsByName.wooden_pickaxe;
  
  if (!plankType || !stickType || !pickaxeType) {
    throw new Error("Required items not available in game data");
  }

  // Check if we have materials
  const planks = bot.inventory.findInventoryItem(plankType.id);
  const sticks = bot.inventory.findInventoryItem(stickType.id);
  
  if (!planks || planks.count < 3) {
    throw new Error("Need at least 3 planks to craft tools");
  }
  
  if (!sticks || sticks.count < 2) {
    // Try to craft sticks first
    try {
      await bot.craft(stickType, 1);
    } catch (err) {
      throw new Error("Need 2 sticks and cannot craft them");
    }
  }

  try {
    await bot.craft(pickaxeType, 1);
    return {
      message: "Successfully crafted wooden pickaxe",
      details: { tool: "wooden_pickaxe" }
    };
  } catch (err) {
    throw new Error(`Failed to craft tools: ${err.message}`);
  }
}

module.exports = {
  executeCraft,
  craftPlanks,
  craftBasicTools
};