// Filename: actions/index.js
// Centralized export for all action modules

const { parseAction } = require('./action-parser');
const { handleAction, executeAction } = require('./action-coordinator');

// Individual action modules (if needed for direct access)
const movementActions = require('./movement-actions');
const gatheringActions = require('./gathering-actions');
const craftingActions = require('./crafting-actions');
const buildingActions = require('./building-actions');
const combatActions = require('./combat-actions');
const inventoryActions = require('./inventory-actions');
const observationActions = require('./observation-actions');

module.exports = {
  // Main functions
  parseAction,
  handleAction,
  executeAction,
  
  // Action modules (for direct access if needed)
  movementActions,
  gatheringActions,
  craftingActions,
  buildingActions,
  combatActions,
  inventoryActions,
  observationActions
};