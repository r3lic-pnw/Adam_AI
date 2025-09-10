// Filename: actions/inventory-actions.js

async function executeDropItem(bot) {
  console.log(`📦 Dropping item`);
  
  const inventory = bot.inventory.items();
  if (inventory.length === 0) {
    throw new Error("Inventory is empty");
  }

  // Drop the first non-essential item
  const nonEssentials = inventory.filter(item => 
    !item.name.includes('sword') && 
    !item.name.includes('pickaxe') &&
    !item.name.includes('food')
  );

  const itemToDrop = nonEssentials[0] || inventory[0];

  try {
    await bot.toss(itemToDrop.type, null, 1);
    return {
      message: `Dropped ${itemToDrop.name}`,
      details: { item: itemToDrop.name }
    };
  } catch (err) {
    throw new Error(`Failed to drop item: ${err.message}`);
  }
}

async function executeEquipTool(bot) {
  console.log(`🔧 Equipping tool`);
  
  // Find tools in inventory
  const tools = bot.inventory.items().filter(item => 
    item.name.includes('pickaxe') || 
    item.name.includes('axe') || 
    item.name.includes('shovel') || 
    item.name.includes('sword')
  );

  if (tools.length === 0) {
    throw new Error("No tools available in inventory");
  }

  const bestTool = tools[0]; // Use first available tool

  try {
    await bot.equip(bestTool, 'hand');
    return {
      message: `Equipped ${bestTool.name}`,
      details: { tool: bestTool.name }
    };
  } catch (err) {
    throw new Error(`Failed to equip tool: ${err.message}`);
  }
}

module.exports = {
  executeDropItem,
  executeEquipTool
};