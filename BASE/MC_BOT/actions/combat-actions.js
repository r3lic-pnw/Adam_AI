// Filename: actions/combat-actions.js

async function executeAttack(bot) {
  console.log(`⚔️ Attacking hostile entities`);
  
  // Find hostile entities nearby
  const hostileEntities = Object.values(bot.entities).filter(entity => 
    entity.mobType && 
    (entity.mobType === 'Hostile' || 
     ['zombie', 'skeleton', 'spider', 'creeper', 'enderman'].includes(entity.name?.toLowerCase())) &&
    entity.position.distanceTo(bot.entity.position) < 16
  );

  if (hostileEntities.length === 0) {
    throw new Error("No hostile entities found nearby");
  }

  // Attack the closest hostile entity
  const target = hostileEntities.reduce((closest, entity) => {
    const distanceToEntity = entity.position.distanceTo(bot.entity.position);
    const distanceToClosest = closest.position.distanceTo(bot.entity.position);
    return distanceToEntity < distanceToClosest ? entity : closest;
  });

  try {
    // Equip best weapon if available
    const weapons = bot.inventory.items().filter(item => 
      item.name.includes('sword') || item.name.includes('axe')
    );
    
    if (weapons.length > 0) {
      await bot.equip(weapons[0], 'hand');
    }

    await bot.attack(target);
    
    return {
      message: `Attacked ${target.name || 'hostile entity'}`,
      details: { target: target.name, position: target.position }
    };
  } catch (err) {
    throw new Error(`Failed to attack: ${err.message}`);
  }
}

module.exports = {
  executeAttack
};