// Filename: actions/gathering-actions.js

// Action execution timeout in milliseconds
const ACTION_TIMEOUT = 30000;

async function executeGather(bot, resource) {
  console.log(`⛏️ Gathering ${resource}`);
  
  if (!bot.collectBlock) {
    throw new Error("CollectBlock plugin not available");
  }

  const mcData = bot.mcData;
  let targetBlocks = [];

  switch (resource) {
    case 'wood':
      targetBlocks = ['oak_log', 'birch_log', 'spruce_log', 'jungle_log', 'acacia_log', 'dark_oak_log'];
      break;
    case 'stone':
      targetBlocks = ['stone', 'cobblestone', 'andesite', 'diorite', 'granite'];
      break;
    case 'dirt':
      targetBlocks = ['dirt', 'grass_block', 'coarse_dirt'];
      break;
    case 'ore':
      targetBlocks = ['coal_ore', 'iron_ore', 'gold_ore', 'diamond_ore', 'redstone_ore'];
      break;
    default:
      throw new Error(`Unknown resource type: ${resource}`);
  }

  // Find the best block to collect
  let targetBlock = null;
  for (const blockName of targetBlocks) {
    const blockType = mcData.blocksByName[blockName];
    if (blockType) {
      const foundBlock = bot.findBlock({
        matching: blockType.id,
        maxDistance: 32
      });
      if (foundBlock) {
        targetBlock = foundBlock;
        break;
      }
    }
  }

  if (!targetBlock) {
    throw new Error(`No ${resource} blocks found within range`);
  }

  // Start collecting
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      bot.collectBlock.cancelTask();
      reject(new Error(`Collection timeout - could not gather ${resource}`));
    }, ACTION_TIMEOUT);

    bot.collectBlock.collect(targetBlock, (err) => {
      clearTimeout(timeout);
      if (err) {
        reject(new Error(`Failed to collect ${resource}: ${err.message}`));
      } else {
        resolve({
          message: `Successfully gathered ${resource}`,
          details: { resource, position: targetBlock.position }
        });
      }
    });
  });
}

module.exports = {
  executeGather
};