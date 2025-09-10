// world-info.js - Comprehensive environmental awareness system

function getVisionData(bot) {
  // console.log("EXEC GETVISIONDATA-WORLDINFO.JS")
  if (!bot || !bot.entity) {
    throw new Error("Bot not available or not spawned");
  }

  const vision = {
    // Basic position and orientation
    position: {
      x: Math.round(bot.entity.position.x * 100) / 100,
      y: Math.round(bot.entity.position.y * 100) / 100,
      z: Math.round(bot.entity.position.z * 100) / 100
    },
    rotation: {
      yaw: Math.round((bot.entity.yaw * 180 / Math.PI) * 100) / 100,
      pitch: Math.round((bot.entity.pitch * 180 / Math.PI) * 100) / 100
    },
    
    // Health and status
    health: bot.health || 0,
    food: bot.food || 0,
    experience: bot.experience || 0,
    
    // Time and weather
    time: getTimeInfo(bot),
    weather: getWeatherInfo(bot),
    
    // Biome information
    biome: getBiomeInfo(bot),
    
    // What the bot is looking at
    targetBlock: getTargetBlock(bot),
    
    // Inventory status
    inventory: getInventoryInfo(bot),
    
    // Movement capabilities
    capabilities: getMovementCapabilities(bot),
    
    // Visible blocks in line of sight
    blocksInSight: getBlocksInSight(bot),
    
    // Nearby entities and players
    entitiesInSight: getEntitiesInSight(bot),
    
    // Immediate surroundings (blocks around the bot)
    surroundings: getSurroundings(bot),
    
    // Any scan errors
    scanError: null
  };

  // console.log(vision);
  return vision;
}

function getTimeInfo(bot) {
  try {
    if (bot.time && typeof bot.time === 'object') {
      const timeOfDay = bot.time.timeOfDay || 0;
      const day = Math.floor((bot.time.age || 0) / 24000);
      
      let phase = "unknown";
      if (timeOfDay >= 0 && timeOfDay < 6000) phase = "morning";
      else if (timeOfDay >= 6000 && timeOfDay < 12000) phase = "day";
      else if (timeOfDay >= 12000 && timeOfDay < 18000) phase = "evening";
      else if (timeOfDay >= 18000 && timeOfDay < 24000) phase = "night";
      
      return {
        timeOfDay: timeOfDay,
        day: day,
        phase: phase
      };
    }
    return { phase: "unknown", day: 0, timeOfDay: 0 };
  } catch (err) {
    console.warn("[Vision] Time info error:", err.message);
    return { phase: "unknown", day: 0, timeOfDay: 0 };
  }
}

function getWeatherInfo(bot) {
  try {
    return {
      isRaining: bot.isRaining || false,
      thunderState: bot.thunderState || 0
    };
  } catch (err) {
    console.warn("[Vision] Weather info error:", err.message);
    return { isRaining: false, thunderState: 0 };
  }
}

function getBiomeInfo(bot) {
  try {
    const block = bot.blockAt(bot.entity.position);
    return block && block.biome ? block.biome.name : "unknown";
  } catch (err) {
    console.warn("[Vision] Biome info error:", err.message);
    return "unknown";
  }
}

function getTargetBlock(bot) {
  try {
    const block = bot.blockAtCursor(5);
    if (block && block.name !== 'air') {
      return {
        name: block.name,
        position: {
          x: block.position.x,
          y: block.position.y,
          z: block.position.z
        },
        material: block.material || null,
        hardness: block.hardness || null
      };
    }
    return null;
  } catch (err) {
    // blockAtCursor might not be available in all versions
    return null;
  }
}

function getInventoryInfo(bot) {
  try {
    const items = bot.inventory.items();
    const itemInHand = bot.heldItem;
    
    let handInfo = null;
    if (itemInHand) {
      handInfo = {
        name: itemInHand.name,
        displayName: itemInHand.displayName,
        count: itemInHand.count,
        durability: itemInHand.durabilityUsed || 0
      };
    }
    
    return {
      itemInHand: handInfo,
      totalItems: items.length,
      slots: items.map(item => ({
        name: item.name,
        count: item.count,
        slot: item.slot
      }))
    };
  } catch (err) {
    console.warn("[Vision] Inventory info error:", err.message);
    return {
      itemInHand: null,
      totalItems: 0,
      slots: []
    };
  }
}

function getMovementCapabilities(bot) {
  try {
    return {
      onGround: bot.entity.onGround || false,
      inWater: bot.entity.inWater || false,
      canFly: false, // Most servers don't allow flight
      canSprint: (bot.food || 0) > 6,
      isJumping: bot.entity.velocity?.y > 0 || false
    };
  } catch (err) {
    console.warn("[Vision] Movement capabilities error:", err.message);
    return {
      onGround: true,
      inWater: false,
      canFly: false,
      canSprint: false,
      isJumping: false
    };
  }
}

function getBlocksInSight(bot) {
  try {
    const botPos = bot.entity.position;
    const yaw = bot.entity.yaw;
    const pitch = bot.entity.pitch;
    
    // Calculate direction vector
    const dirX = -Math.sin(yaw) * Math.cos(pitch);
    const dirY = -Math.sin(pitch);
    const dirZ = Math.cos(yaw) * Math.cos(pitch);
    
    const blocks = [];
    const maxDistance = 20;
    const seen = new Set();
    
    // Raycast in the looking direction
    for (let distance = 1; distance <= maxDistance; distance += 0.5) {
      const x = Math.floor(botPos.x + dirX * distance);
      const y = Math.floor(botPos.y + bot.entity.height * 0.9 + dirY * distance);
      const z = Math.floor(botPos.z + dirZ * distance);
      
      const blockKey = `${x},${y},${z}`;
      if (seen.has(blockKey)) continue;
      seen.add(blockKey);
      
      try {
        const block = bot.blockAt(bot.vec3(x, y, z));
        if (block && block.name !== 'air') {
          const actualDistance = Math.sqrt(
            Math.pow(botPos.x - block.position.x, 2) +
            Math.pow(botPos.y - block.position.y, 2) +
            Math.pow(botPos.z - block.position.z, 2)
          );
          
          blocks.push({
            name: block.name,
            position: block.position,
            distance: Math.round(actualDistance * 10) / 10,
            canBreak: canBreakBlock(bot, block)
          });
          
          if (blocks.length >= 10) break; // Limit results
        }
      } catch (e) {
        // Skip invalid positions
      }
    }
    
    return blocks.sort((a, b) => a.distance - b.distance);
  } catch (err) {
    console.warn("[Vision] Blocks in sight error:", err.message);
    return [];
  }
}

function getEntitiesInSight(bot) {
  try {
    const botPos = bot.entity.position;
    const entities = [];
    
    Object.values(bot.entities).forEach(entity => {
      if (!entity || entity === bot.entity) return;
      
      const distance = Math.sqrt(
        Math.pow(botPos.x - entity.position.x, 2) +
        Math.pow(botPos.y - entity.position.y, 2) +
        Math.pow(botPos.z - entity.position.z, 2)
      );
      
      if (distance <= 20) {
        const entityData = {
          type: entity.name || entity.displayName || 'unknown',
          position: entity.position,
          distance: Math.round(distance * 10) / 10,
          isPlayer: !!entity.username,
          isHostile: isHostileEntity(entity),
          inView: isEntityInView(bot, entity),
          health: entity.health || null
        };
        
        if (entity.username) {
          entityData.name = entity.username;
        }
        
        if (entity.displayName) {
          entityData.mobType = entity.displayName;
        }
        
        entities.push(entityData);
      }
    });
    
    return entities.sort((a, b) => a.distance - b.distance);
  } catch (err) {
    console.warn("[Vision] Entities in sight error:", err.message);
    return [];
  }
}

function getSurroundings(bot) {
  try {
    const pos = bot.entity.position;
    const x = Math.floor(pos.x);
    const y = Math.floor(pos.y);
    const z = Math.floor(pos.z);
    
    const ground = getBlockName(bot, x, y - 1, z);
    const ceiling = getBlockName(bot, x, y + 2, z);
    
    return {
      ground: ground,
      ceiling: ceiling,
      walls: {
        north: getBlockName(bot, x, y, z - 1),
        south: getBlockName(bot, x, y, z + 1),
        east: getBlockName(bot, x + 1, y, z),
        west: getBlockName(bot, x - 1, y, z)
      }
    };
  } catch (err) {
    console.warn("[Vision] Surroundings error:", err.message);
    return {
      ground: 'unknown',
      ceiling: 'unknown',
      walls: { north: 'unknown', south: 'unknown', east: 'unknown', west: 'unknown' }
    };
  }
}

// Helper functions
function getBlockName(bot, x, y, z) {
  try {
    const block = bot.blockAt(bot.vec3(x, y, z));
    return block ? block.name : 'air';
  } catch (err) {
    return 'unknown';
  }
}

function canBreakBlock(bot, block) {
  try {
    if (!block || !bot.mcData) return true; // Assume breakable if unsure
    
    // Some basic unbreakable blocks
    const unbreakableBlocks = ['bedrock', 'barrier', 'command_block', 'end_portal', 'end_portal_frame'];
    return !unbreakableBlocks.includes(block.name);
  } catch (err) {
    return true;
  }
}

function isHostileEntity(entity) {
  if (!entity) return false;
  
  if (entity.displayName === 'Hostile') return true;
  
  const hostileMobs = [
    'zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch',
    'zombie_villager', 'husk', 'stray', 'cave_spider', 'silverfish',
    'blaze', 'ghast', 'magma_cube', 'slime', 'phantom', 'drowned'
  ];
  
  const entityName = (entity.name || '').toLowerCase();
  return hostileMobs.some(mob => entityName.includes(mob));
}

function isEntityInView(bot, entity) {
  try {
    // Simple line of sight check
    const botPos = bot.entity.position;
    const entityPos = entity.position;
    
    // Check if there are blocks between bot and entity
    const dx = entityPos.x - botPos.x;
    const dy = entityPos.y - botPos.y;
    const dz = entityPos.z - botPos.z;
    const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
    
    if (distance > 20) return false;
    
    // Simple check - if close enough, consider in view
    return distance < 10;
  } catch (err) {
    return false;
  }
}

module.exports = {
  getVisionData
};