import { fromPromise } from "xstate";
import { ActionComposer } from "../services/action-composer";
import { ActionExecutor } from "../services/action-executor";
import { SignalEvaluator } from "../services/signal-evaluator";
import { ThreatProcessor } from "../services/threat-processor";
import { HorusContext } from "./types";

// Create instances of our services
const signalEvaluator = new SignalEvaluator();
const threatProcessor = new ThreatProcessor();
const actionComposer = new ActionComposer({
  Beefy: ["beefyUSDC-USDT", "beefyWBTC-EIGEN", "beefyUSDC-EIGEN"],
  UniswapV3: [
    "UNI-V3-USDC-USDT-500",
    "UNI-V3-WBTC-EIGEN-500",
    "UNI-V3-USDC-EIGEN-500",
  ],
});
const actionExecutor = new ActionExecutor();

// Define actors using fromPromise
const evaluateSignalsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log("Evaluating signal:", input.context.currentSignal);
    if (!input.context.currentSignal) {
      throw new Error("No signal to evaluate");
    }

    try {
      const result = await signalEvaluator.evaluateSignal(
        input.context.currentSignal
      );
      console.log("Signal evaluation result:", result);
      return result;
    } catch (error) {
      console.error("Error evaluating signal:", error);
      throw error;
    }
  }
);

const processThreatsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log("Processing threat:", input.context.detectedThreat);
    if (!input.context.detectedThreat) {
      throw new Error("No threat to process");
    }

    try {
      const result = await threatProcessor.processThreat(
        input.context.detectedThreat
      );
      console.log("Threat processing result:", result);
      return result;
    } catch (error) {
      console.error("Error processing threat:", error);
      throw error;
    }
  }
);

const composeActionsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log("Composing actions for threat:", input.context.detectedThreat);
    if (!input.context.detectedThreat) {
      throw new Error("No threat to compose actions for");
    }

    try {
      const result = await actionComposer.composeActions(
        input.context.detectedThreat
      );
      console.log("Action composition result:", result);
      return result;
    } catch (error) {
      console.error("Error composing actions:", error);
      throw error;
    }
  }
);

const executeActionsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log("Executing actions:", input.context.actionPlan);
    if (!input.context.actionPlan || input.context.actionPlan.length === 0) {
      throw new Error("No actions to execute");
    }

    try {
      const result = await actionExecutor.executeActions(
        input.context.actionPlan
      );
      console.log("Action execution result:", result);
      return result;
    } catch (error) {
      console.error("Error executing actions:", error);
      throw error;
    }
  }
);

// Export the actors object for use in the machine
export const actors = {
  evaluateSignals: evaluateSignalsActor,
  processThreats: processThreatsActor,
  composeActions: composeActionsActor,
  executeActions: executeActionsActor,
};
