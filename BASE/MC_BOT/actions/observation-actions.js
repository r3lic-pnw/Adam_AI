// Filename: actions/observation-actions.js

function executeLookAround(bot) {
  console.log(`👀 Looking around`);
  
  // Get nearby entities and blocks
  const nearbyEntities = Object.values(bot.entities)
    .filter(entity => entity.position.distanceTo(bot.entity.position) < 10)
    .map(entity => entity.name || entity.mobType || 'unknown');

  const surroundings = [];
  for (let x = -2; x <= 2; x++) {
    for (let z = -2; z <= 2; z++) {
      const block = bot.blockAt(bot.entity.position.offset(x, 0, z));
      if (block && block.name !== 'air') {
        surroundings.push(block.name);
      }
    }
  }

  const uniqueBlocks = [...new Set(surroundings)];
  const uniqueEntities = [...new Set(nearbyEntities)];

  return {
    message: "Completed area scan",
    details: {
      nearbyBlocks: uniqueBlocks,
      nearbyEntities: uniqueEntities,
      position: bot.entity.position
    }
  };
}

module.exports = {
  executeLookAround
};