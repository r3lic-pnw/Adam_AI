// Filename: actions/building-actions.js

async function executePlaceBlock(bot) {
  console.log(`🧱 Placing block`);
  
  // Find a block in inventory to place
  const inventory = bot.inventory.items();
  const placeableBlocks = inventory.filter(item => 
    item.name.includes('dirt') || 
    item.name.includes('stone') || 
    item.name.includes('planks') ||
    item.name.includes('cobblestone')
  );

  if (placeableBlocks.length === 0) {
    throw new Error("No placeable blocks in inventory");
  }

  const blockToPlace = placeableBlocks[0];
  
  // Find a position to place the block (in front of bot)
  const targetPosition = bot.entity.position.offset(1, 0, 0);
  const targetBlock = bot.blockAt(targetPosition);
  
  if (!targetBlock || targetBlock.name !== 'air') {
    throw new Error("Cannot place block - position is not empty");
  }

  try {
    // Find a reference block to place against
    const referenceBlock = bot.blockAt(targetPosition.offset(0, -1, 0));
    if (referenceBlock && referenceBlock.name !== 'air') {
      await bot.equip(blockToPlace, 'hand');
      await bot.placeBlock(referenceBlock, new bot.Vec3(0, 1, 0));
      
      return {
        message: `Successfully placed ${blockToPlace.name}`,
        details: { block: blockToPlace.name, position: targetPosition }
      };
    } else {
      throw new Error("No suitable surface to place block on");
    }
  } catch (err) {
    throw new Error(`Failed to place block: ${err.message}`);
  }
}

async function executeBreakBlock(bot) {
  console.log(`⛏️ Breaking block`);
  
  // Find the block the bot is looking at
  const targetBlock = bot.blockAtCursor(5);
  
  if (!targetBlock || targetBlock.name === 'air') {
    throw new Error("No block to break");
  }

  if (targetBlock.name === 'bedrock') {
    throw new Error("Cannot break bedrock");
  }

  try {
    await bot.dig(targetBlock);
    return {
      message: `Successfully broke ${targetBlock.name}`,
      details: { block: targetBlock.name, position: targetBlock.position }
    };
  } catch (err) {
    throw new Error(`Failed to break block: ${err.message}`);
  }
}

module.exports = {
  executePlaceBlock,
  executeBreakBlock
};