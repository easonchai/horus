require('dotenv').config();
const dalService = require("./dal.service");
const oracleService = require("./oracle.service");

const MAX_DEVIATION = 0.01
async function validate(proofOfTask) {

  try {
      const taskResult = await dalService.getIPfsTask(proofOfTask);
      var data = await oracleService.getPrice("USDC/USDT");
      let isApproved = true;
      const deviation = Math.abs(taskResult.price - 1.0)
      if(deviation >= MAX_DEVIATION) {
        isApproved = false;
      }
      return isApproved;
    } catch (err) {
      console.error(err?.message);
      return false;
    }
  }
  
  module.exports = {
    validate,
  }