// Filename: bot-actions.js (refactored)
// This file now serves as the main entry point, importing from the action modules

const { parseAction } = require('./actions/action-parser');
const { handleAction } = require('./actions/action-coordinator');

// Re-export the main functions for backwards compatibility
module.exports = {
  parseAction,
  handleAction
};