// Filename: actions/gathering-actions.js
// Enhanced version with proper tool management

const ACTION_TIMEOUT = 30000;

async function executeGather(bot, resource) {
  console.log(`⛏️ Gathering ${resource}`);
  
  // Always use basic gathering - it's more reliable
  return await executeBasicGather(bot, resource);
}

// Find and equip the best tool for the job
async function equipBestTool(bot, resource) {
  const inventory = bot.inventory.items();
  let bestTool = null;
  
  // Define tool preferences for each resource
  const toolPreferences = {
    dirt: ['shovel', 'spade'],
    stone: ['pickaxe', 'pick'],
    wood: ['axe', 'hatchet'],
    ore: ['pickaxe', 'pick']
  };
  
  const preferredTools = toolPreferences[resource] || [];
  
  // Find the best tool in inventory
  for (const toolType of preferredTools) {
    const tool = inventory.find(item => 
      item.name.toLowerCase().includes(toolType) && 
      !item.name.includes('broken')
    );
    if (tool) {
      bestTool = tool;
      break;
    }
  }
  
  // If no specific tool found, try to find any tool that might work
  if (!bestTool) {
    const anyTool = inventory.find(item => 
      (item.name.includes('shovel') || 
       item.name.includes('pickaxe') || 
       item.name.includes('axe')) &&
      !item.name.includes('broken')
    );
    if (anyTool) {
      bestTool = anyTool;
    }
  }
  
  // Equip the tool if found
  if (bestTool) {
    try {
      await bot.equip(bestTool, 'hand');
      console.log(`🔧 Equipped ${bestTool.name} for ${resource} gathering`);
      return bestTool.name;
    } catch (err) {
      console.warn(`⚠️ Failed to equip ${bestTool.name}: ${err.message}`);
    }
  }
  
  // If no tools available, unequip current item (use hands)
  try {
    await bot.unequip('hand');
    console.log(`✋ Using hands to gather ${resource} (no suitable tools found)`);
    return 'hands';
  } catch (err) {
    console.log(`🤷 Will use current item: ${bot.heldItem ? bot.heldItem.name : 'none'}`);
    return bot.heldItem ? bot.heldItem.name : 'hands';
  }
}

// Basic gathering using bot.dig() - most reliable method
async function executeBasicGather(bot, resource) {
  console.log(`🔧 Using basic gathering method for ${resource}`);
  
  const mcData = bot.mcData;
  if (!mcData || !mcData.blocksByName) {
    throw new Error("Minecraft data not available");
  }

  let targetBlocks = [];
  switch (resource) {
    case 'wood':
      targetBlocks = ['oak_log', 'birch_log', 'spruce_log', 'jungle_log', 'acacia_log', 'dark_oak_log'];
      break;
    case 'stone':
      targetBlocks = ['stone', 'cobblestone', 'andesite', 'diorite', 'granite'];
      break;
    case 'dirt':
      targetBlocks = ['dirt', 'grass_block', 'coarse_dirt', 'podzol'];
      break;
    case 'ore':
      targetBlocks = ['coal_ore', 'iron_ore', 'gold_ore', 'diamond_ore', 'redstone_ore', 'lapis_ore'];
      break;
    default:
      throw new Error(`Unknown resource type: ${resource}`);
  }

  // Find nearby block within reasonable range
  let targetBlock = null;
  let blockTypeName = '';
  
  for (const blockName of targetBlocks) {
    const blockType = mcData.blocksByName[blockName];
    if (blockType) {
      targetBlock = bot.findBlock({
        matching: blockType.id,
        maxDistance: 16
      });
      if (targetBlock) {
        blockTypeName = blockName;
        console.log(`🎯 Found ${blockName} at ${targetBlock.position}`);
        break;
      }
    }
  }

  if (!targetBlock) {
    throw new Error(`No ${resource} found within 16 blocks`);
  }

  // Equip the best tool for this resource
  const equippedTool = await equipBestTool(bot, resource);

  // Check if we need to move closer
  const distance = bot.entity.position.distanceTo(targetBlock.position);
  if (distance > 5) {
    console.log(`🚶 Moving closer to ${blockTypeName} (${distance.toFixed(1)} blocks away)`);
    
    if (bot.pathfinder) {
      try {
        const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
        const defaultMove = new Movements(bot, mcData);
        bot.pathfinder.setMovements(defaultMove);
        
        const goal = new goals.GoalNear(targetBlock.position.x, targetBlock.position.y, targetBlock.position.z, 3);
        
        // Wait for movement to complete
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            bot.pathfinder.setGoal(null);
            resolve(); // Don't fail if movement times out, just try digging from current position
          }, 10000);

          bot.pathfinder.setGoal(goal);

          const onGoalReached = () => {
            clearTimeout(timeout);
            bot.pathfinder.removeListener('goal_reached', onGoalReached);
            bot.pathfinder.removeListener('path_stop', onPathStop);
            resolve();
          };

          const onPathStop = () => {
            clearTimeout(timeout);
            bot.pathfinder.removeListener('goal_reached', onGoalReached);
            bot.pathfinder.removeListener('path_stop', onPathStop);
            resolve(); // Continue even if path stops
          };

          bot.pathfinder.on('goal_reached', onGoalReached);
          bot.pathfinder.on('path_stop', onPathStop);
        });
      } catch (movementError) {
        console.warn(`⚠️ Movement failed: ${movementError.message}, trying to dig from current position`);
      }
    }
  }

  // Check final distance
  const finalDistance = bot.entity.position.distanceTo(targetBlock.position);
  if (finalDistance > 6) {
    throw new Error(`Cannot reach ${resource} block - too far away (${finalDistance.toFixed(1)} blocks)`);
  }

  // Perform the actual digging with enhanced error handling
  console.log(`⛏️ Starting to dig ${blockTypeName} with ${equippedTool}`);
  
  return new Promise((resolve, reject) => {
    // Shorter timeout for individual dig attempts
    const timeout = setTimeout(() => {
      console.warn(`⏰ Dig timeout for ${blockTypeName}`);
      reject(new Error(`Digging took too long - the ${resource} block may be too hard or protected`));
    }, 10000);

    // Check if the block still exists and is the same
    const currentBlock = bot.blockAt(targetBlock.position);
    if (!currentBlock || currentBlock.name === 'air') {
      clearTimeout(timeout);
      reject(new Error(`${resource} block is no longer there`));
      return;
    }
    
    if (targetBlocks.includes(currentBlock.name)) {
      console.log(`✅ Confirmed block is still ${currentBlock.name}`);
    } else {
      clearTimeout(timeout);
      reject(new Error(`Block changed from ${blockTypeName} to ${currentBlock.name}`));
      return;
    }

    // Start digging
    bot.dig(currentBlock, (err) => {
      clearTimeout(timeout);
      if (err) {
        console.error(`❌ Dig error: ${err.message}`);
        
        if (err.message.includes('far away') || err.message.includes('reach')) {
          reject(new Error(`${resource} block is too far away to dig (${finalDistance.toFixed(1)} blocks)`));
        } else if (err.message.includes('not diggable') || err.message.includes('cannot')) {
          reject(new Error(`Cannot dig ${resource} block - may need a better tool or the block is protected`));
        } else if (err.message.includes('line of sight')) {
          reject(new Error(`Cannot see the ${resource} block clearly - something is in the way`));
        } else {
          reject(new Error(`Failed to dig ${resource}: ${err.message}`));
        }
      } else {
        console.log(`✅ Successfully dug ${blockTypeName} using ${equippedTool}`);
        resolve({
          message: `Successfully gathered ${resource} (${blockTypeName}) using ${equippedTool}`,
          details: { 
            resource, 
            blockType: blockTypeName,
            position: targetBlock.position,
            tool: equippedTool,
            distance: finalDistance.toFixed(1),
            method: 'basic_dig'
          }
        });
      }
    });
  });
}

// Utility function to check what tools are available
function checkAvailableTools(bot) {
  const inventory = bot.inventory.items();
  const tools = {
    shovels: [],
    pickaxes: [],
    axes: [],
    other: []
  };
  
  inventory.forEach(item => {
    if (item.name.includes('shovel') || item.name.includes('spade')) {
      tools.shovels.push(item.name);
    } else if (item.name.includes('pickaxe') || item.name.includes('pick')) {
      tools.pickaxes.push(item.name);
    } else if (item.name.includes('axe')) {
      tools.axes.push(item.name);
    } else if (item.name.includes('sword') || item.name.includes('hoe')) {
      tools.other.push(item.name);
    }
  });
  
  return tools;
}

module.exports = {
  executeGather,
  executeBasicGather,
  equipBestTool,
  checkAvailableTools
};