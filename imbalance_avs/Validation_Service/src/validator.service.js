require('dotenv').config();
const dalService = require("./dal.service");
const oracleService = require("./oracle.service");

const MAX_DEVIATION = 0.01
async function validate(proofOfTask) {
  try {

      // Retrieve performer submission
      const taskResult = await dalService.getIPfsTask(proofOfTask);

      // Retrieve the submission ourselves to validate 
      const sourceOfTruth = await oracleService.getPrice(taskResult.pair);

      // Check if our source of truth depgged
      const depegged = false
      const deviation = Math.abs(sourceOfTruth.price - 1.0)
      if(deviation >= MAX_DEVIATION) {
        depegged = true;
      }
      
      // Performer logic should be same as ours, so if it truly did depeg, then it will match on our
      // validators as well
      return taskResult.depegged == depegged;
    } catch (err) {
      console.error(err?.message);
      return false;
    }
  }
  
  module.exports = {
    validate,
  }