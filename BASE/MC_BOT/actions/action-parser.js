// Filename: actions/action-parser.js

// Enhanced action parsing with better natural language understanding
function parseAction(text) {
  if (!text || typeof text !== 'string') {
    return null;
  }

  const input = text.toLowerCase().trim();
  
  // Movement actions
  if (input.includes('go to') || input.includes('move to') || input.includes('travel to')) {
    const coords = input.match(/(-?\d+)[\s,]+(-?\d+)(?:[\s,]+(-?\d+))?/);
    if (coords) {
      const x = parseInt(coords[1]);
      const y = parseInt(coords[2]);
      const z = coords[3] ? parseInt(coords[3]) : null;
      return { type: 'goto', x, y, z };
    }
  }
  
  if (input.includes('follow player') || input.includes('follow you')) {
    return { type: 'follow' };
  }
  
  if (input.includes('go near player') || input.includes('come over') || input.includes('approach')) {
    return { type: 'approach' };
  }
  
  if (input.includes('stop') || input.includes('halt') || input.includes('wait')) {
    return { type: 'stop' };
  }

  // Resource gathering actions
  if (input.includes('gather wood') || input.includes('collect wood') || input.includes('chop wood')) {
    return { type: 'gather', resource: 'wood' };
  }
  
  if (input.includes('gather stone') || input.includes('mine stone') || input.includes('collect stone')) {
    return { type: 'gather', resource: 'stone' };
  }
  
  if (input.includes('gather dirt') || input.includes('dig dirt') || input.includes('collect dirt')) {
    return { type: 'gather', resource: 'dirt' };
  }
  
  if (input.includes('gather ore') || input.includes('mine ore')) {
    return { type: 'gather', resource: 'ore' };
  }

  // Crafting actions
  if (input.includes('craft planks') || input.includes('make planks')) {
    return { type: 'craft', item: 'planks' };
  }
  
  if (input.includes('craft tools') || input.includes('make tools')) {
    return { type: 'craft', item: 'tools' };
  }

  // Building actions
  if (input.includes('place block') || input.includes('put down block')) {
    return { type: 'place_block' };
  }
  
  if (input.includes('break block') || input.includes('mine block')) {
    return { type: 'break_block' };
  }

  // Combat actions
  if (input.includes('attack hostile') || input.includes('fight') || input.includes('defend')) {
    return { type: 'attack' };
  }

  // Inventory actions
  if (input.includes('drop item') || input.includes('throw item')) {
    return { type: 'drop_item' };
  }
  
  if (input.includes('equip tool') || input.includes('hold tool')) {
    return { type: 'equip_tool' };
  }

  // Observation actions
  if (input.includes('look around') || input.includes('scan area')) {
    return { type: 'look_around' };
  }
  
  if (input.includes('explore area') || input.includes('search around')) {
    return { type: 'explore' };
  }

  return { type: 'follow' }; // Default action to follow player if none matched
}

module.exports = {
  parseAction
};