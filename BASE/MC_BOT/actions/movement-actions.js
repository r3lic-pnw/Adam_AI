// Filename: actions/movement-actions.js
const { pathfinderModule } = require('../bot');

// Movement timeout in milliseconds
const MOVEMENT_TIMEOUT = 120000;

async function executeGoto(bot, action) {
  if (!bot.pathfinder || !pathfinderModule) {
    throw new Error("Pathfinder not available");
  }

  const { x, y, z } = action;
  const targetY = y !== null ? y : bot.entity.position.y;
  const targetZ = z !== null ? z : bot.entity.position.z;

  console.log(`🚶 Moving to coordinates: ${x}, ${targetY}, ${targetZ}`);
  
  const goal = new pathfinderModule.goals.GoalBlock(x, targetY, targetZ);
  bot.pathfinder.setGoal(goal);

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      bot.pathfinder.setGoal(null);
      reject(new Error("Movement timeout - destination may be unreachable"));
    }, MOVEMENT_TIMEOUT);

    bot.once('goal_reached', () => {
      clearTimeout(timeout);
      resolve({
        message: `Successfully moved to ${x}, ${targetY}, ${targetZ}`,
        details: { coordinates: { x, y: targetY, z: targetZ } }
      });
    });

    bot.once('path_update', (results) => {
      if (results.status === 'noPath') {
        clearTimeout(timeout);
        bot.pathfinder.setGoal(null);
        reject(new Error(`Cannot find path to ${x}, ${targetY}, ${targetZ}`));
      }
    });
  });
}

async function executeFollow(bot) {
  const players = Object.values(bot.players).filter(p => p.entity && p.username !== bot.username);
  
  if (players.length === 0) {
    throw new Error("No players found to follow");
  }

  const target = players[0]; // Follow first available player
  console.log(`👥 Following player: ${target.username}`);

  if (!bot.pathfinder || !pathfinderModule) {
    throw new Error("Pathfinder not available");
  }

  const goal = new pathfinderModule.goals.GoalFollow(target.entity, 2);
  bot.pathfinder.setGoal(goal);

  return {
    message: `Now following ${target.username}`,
    details: { target: target.username }
  };
}

async function executeApproach(bot) {
  const players = Object.values(bot.players).filter(p => p.entity && p.username !== bot.username);
  
  if (players.length === 0) {
    throw new Error("No players found to approach");
  }

  const target = players[0];
  console.log(`🏃 Approaching player: ${target.username}`);

  if (!bot.pathfinder || !pathfinderModule) {
    throw new Error("Pathfinder not available");
  }

  const goal = new pathfinderModule.goals.GoalNear(target.entity.position.x, target.entity.position.y, target.entity.position.z, 3);
  bot.pathfinder.setGoal(goal);

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      bot.pathfinder.setGoal(null);
      reject(new Error("Approach timeout - could not reach player"));
    }, MOVEMENT_TIMEOUT);

    bot.once('goal_reached', () => {
      clearTimeout(timeout);
      resolve({
        message: `Successfully approached ${target.username}`,
        details: { target: target.username }
      });
    });

    bot.once('path_update', (results) => {
      if (results.status === 'noPath') {
        clearTimeout(timeout);
        bot.pathfinder.setGoal(null);
        reject(new Error(`Cannot find path to ${target.username}`));
      }
    });
  });
}

function executeStop(bot) {
  console.log(`⏹️ Stopping all activities`);
  
  // Stop pathfinding
  if (bot.pathfinder) {
    bot.pathfinder.setGoal(null);
  }
  
  // Stop any attack
  bot.pvp?.stop();
  
  // Stop collecting
  bot.collectBlock?.cancelTask();

  return {
    message: "Stopped all activities",
    details: { stopped: ["movement", "combat", "collection"] }
  };
}

async function executeExplore(bot) {
  console.log(`🗺️ Exploring area`);
  
  if (!bot.pathfinder || !pathfinderModule) {
    throw new Error("Pathfinder not available");
  }

  // Generate a random exploration point within reasonable distance
  const currentPos = bot.entity.position;
  const exploreDistance = 20;
  const angle = Math.random() * Math.PI * 2;
  const distance = 10 + Math.random() * exploreDistance;
  
  const targetX = Math.floor(currentPos.x + Math.cos(angle) * distance);
  const targetZ = Math.floor(currentPos.z + Math.sin(angle) * distance);
  const targetY = currentPos.y;

  const goal = new pathfinderModule.goals.GoalBlock(targetX, targetY, targetZ);
  bot.pathfinder.setGoal(goal);

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      bot.pathfinder.setGoal(null);
      resolve({
        message: "Exploration timeout - discovered new area",
        details: { exploredTo: { x: targetX, y: targetY, z: targetZ } }
      });
    }, 30000); // 30 second timeout for exploration

    bot.once('goal_reached', () => {
      clearTimeout(timeout);
      resolve({
        message: `Successfully explored to ${targetX}, ${targetY}, ${targetZ}`,
        details: { exploredTo: { x: targetX, y: targetY, z: targetZ } }
      });
    });

    bot.once('path_update', (results) => {
      if (results.status === 'noPath') {
        clearTimeout(timeout);
        bot.pathfinder.setGoal(null);
        resolve({
          message: "Could not reach exploration target - found obstacle",
          details: { attemptedTarget: { x: targetX, y: targetY, z: targetZ } }
        });
      }
    });
  });
}

module.exports = {
  executeGoto,
  executeFollow,
  executeApproach,
  executeStop,
  executeExplore
};