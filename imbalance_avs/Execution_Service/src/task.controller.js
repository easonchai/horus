"use strict";
const { Router } = require("express")
const CustomError = require("./utils/validateError");
const CustomResponse = require("./utils/validateResponse");
const oracleService = require("./oracle.service");
const dalService = require("./dal.service");

const router = Router()

const MAX_DEVIATION = 0.01
router.post("/execute", async (req, res) => {
    console.log("Executing task");

    try {
        const pair = "USDC/USDT"
        var taskDefinitionId = Number(req.body.taskDefinitionId) || 0;
        console.log(`taskDefinitionId: ${taskDefinitionId}`);

        const result = await oracleService.getPrice(pair);
        result.price = req.body.fakePrice || result.price;
        let depegged = false;
        const deviation = Math.abs(result.price - 1.0)
        if(deviation >= MAX_DEVIATION) {
          depegged = true;
        }
        // We add entropy so that way a fresh fetch is published and fresh task id is generated, as ipfs generates id based off content (i think)
        const cid = await dalService.publishJSONToIpfs({...result, depegged, pair, entropy: Date.now().toString() });
        const data = "hello";
        await dalService.sendTask(cid, data, taskDefinitionId);
        return res.status(200).send(new CustomResponse({proofOfTask: cid, data: data, taskDefinitionId: taskDefinitionId, depegged}, "Task executed successfully"));
    } catch (error) {
        console.log(error)
        return res.status(500).send(new CustomError("Something went wrong", {}));
    }
})


module.exports = router
