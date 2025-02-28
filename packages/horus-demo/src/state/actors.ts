import { fromPromise } from "xstate";
import { Action, SignalEvaluationResult, Threat } from "../models/types";
import { ActionComposer } from "../services/action-composer";
import { ActionExecutor } from "../services/action-executor";
import { ProtocolService } from "../services/protocol-service";
import { SignalEvaluator } from "../services/signal-evaluator";
import { ThreatProcessor } from "../services/threat-processor";
import { HorusContext } from "./types";

// Create instances of our services
const signalEvaluator = new SignalEvaluator();
const threatProcessor = new ThreatProcessor();
const actionComposer = new ActionComposer(ProtocolService.getDependencyGraph());
const actionExecutor = new ActionExecutor();

/**
 * Actor for evaluating signals to detect threats
 * Enhanced with better error handling for edge cases
 */
const evaluateSignalsActor = fromPromise(
  async ({
    input,
  }: {
    input: { context: HorusContext };
  }): Promise<SignalEvaluationResult> => {
    console.log("Evaluating signal:", input.context.currentSignal);

    // Input validation with helpful error message
    if (!input.context.currentSignal) {
      const error = new Error("No signal to evaluate");
      console.error(
        "[evaluateSignalsActor] Input validation failed:",
        error.message
      );
      throw error;
    }

    try {
      const result = await signalEvaluator.evaluateSignal(
        input.context.currentSignal
      );

      // Ensure result has expected structure to prevent state machine errors
      if (result.isThreat === undefined) {
        console.warn(
          "[evaluateSignalsActor] Signal evaluation result missing isThreat property"
        );
        return { isThreat: false }; // Default to no threat if structure is invalid
      }

      // Handle edge case where isThreat is true but threat is undefined
      if (result.isThreat && !result.threat) {
        console.warn(
          "[evaluateSignalsActor] Threat flagged but no threat details provided"
        );
        // Create a minimal threat object to prevent downstream errors
        return {
          isThreat: true,
          threat: {
            description: `Potential unnamed threat detected: ${input.context.currentSignal.content}`,
            affectedProtocols: [],
            affectedTokens: ["unknown"],
            chain: "ethereum",
            severity: "medium",
          },
        };
      }

      console.log("[evaluateSignalsActor] Signal evaluation result:", result);
      return result;
    } catch (error) {
      // Enhanced error logging
      console.error("[evaluateSignalsActor] Error evaluating signal:", error);

      // Return a properly structured error result instead of throwing
      // This allows the state machine to handle the error gracefully
      return {
        isThreat: false,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }
);

/**
 * Actor for processing detected threats
 * Enhanced with better error handling
 */
const processThreatsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }): Promise<Threat> => {
    console.log(
      "[processThreatsActor] Processing threat:",
      input.context.detectedThreat
    );

    // Input validation with helpful error message
    if (!input.context.detectedThreat) {
      const error = new Error("No threat to process");
      console.error(
        "[processThreatsActor] Input validation failed:",
        error.message
      );
      throw error;
    }

    try {
      const result = await threatProcessor.processThreat(
        input.context.detectedThreat
      );
      console.log("[processThreatsActor] Threat processing result:", result);
      return result;
    } catch (error) {
      console.error("[processThreatsActor] Error processing threat:", error);

      // In case of error, return the original threat rather than failing completely
      console.warn(
        "[processThreatsActor] Returning original threat due to processing error"
      );
      return input.context.detectedThreat;
    }
  }
);

/**
 * Actor for composing actions based on detected threats
 * Enhanced with better error handling and fallback
 */
const composeActionsActor = fromPromise(
  async ({
    input,
  }: {
    input: { context: HorusContext };
  }): Promise<Action[]> => {
    console.log(
      "[composeActionsActor] Composing actions for threat:",
      input.context.detectedThreat
    );

    // Input validation with helpful error message
    if (!input.context.detectedThreat) {
      const error = new Error("No threat to compose actions for");
      console.error(
        "[composeActionsActor] Input validation failed:",
        error.message
      );
      throw error;
    }

    try {
      const result = await actionComposer.composeActions(
        input.context.detectedThreat
      );

      console.log("[composeActionsActor] Action composition result:", result);

      // Handle empty actions result
      if (!result || result.length === 0) {
        console.warn("[composeActionsActor] No actions generated for threat");
        return [];
      }

      return result;
    } catch (error) {
      console.error("[composeActionsActor] Error composing actions:", error);

      // Return empty array instead of throwing, allowing state machine to continue
      return [];
    }
  }
);

/**
 * Actor for executing composed actions
 * Enhanced with better error handling
 */
const executeActionsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log(
      "[executeActionsActor] Executing actions:",
      input.context.actionPlan
    );

    // Input validation with helpful error message
    if (!input.context.actionPlan || input.context.actionPlan.length === 0) {
      const error = new Error("No actions to execute");
      console.error(
        "[executeActionsActor] Input validation failed:",
        error.message
      );
      throw error;
    }

    try {
      const result = await actionExecutor.executeActions(
        input.context.actionPlan
      );
      console.log("[executeActionsActor] Action execution result:", result);
      return result;
    } catch (error) {
      console.error("[executeActionsActor] Error executing actions:", error);

      // Return partial results if possible
      return input.context.actionPlan.map((action) => ({
        success: false,
        txHash: "",
        action,
        error: error instanceof Error ? error.message : String(error),
      }));
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
