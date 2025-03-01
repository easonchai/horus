import {
  ViemWalletProvider,
  WalletProvider,
  walletActionProvider,
} from "@coinbase/agentkit";
import { fromPromise } from "xstate";
import { Action, SignalEvaluationResult, Threat } from "../models/types";
import { evaluateTweetsActionProvider } from "../providers/tweet-evaluation.provider";
import { actionRecommendationSchema, threatAnalysisSchema } from "../schemas";
import { ActionComposer } from "../services/action-composer";
import { ActionExecutor } from "../services/action-executor";
import { AgentService } from "../services/agent-service";
import { DependencyGraphService } from "../services/dependency-graph-service";
import { WalletService } from "../services/wallet-service";
import { HorusContext } from "./types";

// Setup wallet service for AgentKit integration
const walletService = new WalletService();
const walletClient = walletService.getWalletClient();
const walletProvider: WalletProvider | undefined = walletClient
  ? new ViemWalletProvider(walletClient)
  : undefined;

// Create instances of our services with proper configuration
const agentService = new AgentService({
  walletProvider: walletProvider as WalletProvider,
  actionProviders: [evaluateTweetsActionProvider()],
  systemMessage:
    "You are a specialized security analyst for decentralized finance (DeFi) protocols analyzing tweets for security threats.",
});

// Create a dedicated service for action composition
const actionCompositionAgent = new AgentService({
  walletProvider: walletProvider as WalletProvider,
  actionProviders: [walletActionProvider()],
  systemMessage:
    "You are a specialized security response coordinator for decentralized finance (DeFi) protocols. Your role is to recommend specific actions to mitigate detected security threats.",
});

// Create action composer and executor services
const actionComposer = new ActionComposer();
const actionExecutor = new ActionExecutor();

/**
 * Actor for evaluating signals to detect threats
 * Uses AgentService with AgentKit integration and structured data from generateObject
 */
export const evaluateSignalsActor = fromPromise(
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

    // Store the signal in a local variable to satisfy TypeScript
    const signal = input.context.currentSignal;

    try {
      // Initialize AgentService if not already initialized
      await agentService.initialize().catch((error) => {
        console.warn(
          "[evaluateSignalsActor] Failed to initialize AgentService:",
          error
        );
        // Continue execution - we'll use text-based analysis as fallback
      });

      // Get dependency graph data for context
      const dependencyGraph = DependencyGraphService.getDependencyGraph();
      const dependencyGraphString = JSON.stringify(dependencyGraph, null, 2);

      // Create the system prompt for security analysis
      const systemPrompt =
        "You are a specialized security analyst for decentralized finance (DeFi) protocols. Your task is to analyze tweets for security threats, exploits, or vulnerabilities that might affect blockchain protocols or tokens.";

      // Create the user prompt with the signal and dependency graph
      const prompt = `
      Please analyze this tweet for potential security threats:
      
      "${signal.content}"
      
      Our project depends on these protocols and tokens:
      ${dependencyGraphString}
      
      Determine if this tweet describes a real security threat to any blockchain protocol or token.
      Focus particularly on threats that might affect tokens or protocols in our dependency graph.
      
      Respond with structured data indicating whether this is a threat and details if it is.
      `;

      // Use our generateObject method with the threatAnalysisSchema and options object
      const result = await agentService.generateObject({
        prompt,
        schema: threatAnalysisSchema,
        systemPrompt,
        temperature: 0.1, // Lower temperature for more consistent results
      });

      console.log("[evaluateSignalsActor] Threat analysis result:", result);

      // Convert the structured result to SignalEvaluationResult
      if (result.isThreat && result.threatDetails) {
        // Extract the threat details into our Threat model
        const threat: Threat = {
          description: result.threatDetails.description,
          affectedProtocols: result.threatDetails.affectedProtocols,
          affectedTokens: result.threatDetails.affectedTokens,
          chain: result.threatDetails.chain,
          severity: result.threatDetails.severity,
        };

        return {
          isThreat: true,
          threat,
          analysisText: JSON.stringify(result.threatDetails),
        };
      } else {
        // No threat detected
        return {
          isThreat: false,
          analysisText: "No security threat detected in the signal.",
        };
      }
    } catch (error) {
      // Enhanced error logging
      console.error("[evaluateSignalsActor] Error evaluating signal:", error);

      // Fallback to basic keyword-based evaluation if AgentService fails
      if (input.context.currentSignal) {
        const threatKeywords = [
          "vulnerability",
          "exploit",
          "attack",
          "hacked",
          "security",
          "breach",
          "risk",
          "urgent",
          "compromise",
          "critical",
          "emergency",
        ];

        const content = input.context.currentSignal.content.toLowerCase();
        const isSimpleThreat = threatKeywords.some((keyword) =>
          content.includes(keyword.toLowerCase())
        );

        if (isSimpleThreat) {
          console.log(
            "[evaluateSignalsActor] Threat detected via keyword fallback"
          );
          return {
            isThreat: true,
            threat: {
              description: `Potential threat detected via keyword match: ${signal.content}`,
              affectedProtocols: [],
              affectedTokens: [],
              chain: "ethereum",
              severity: "medium",
            },
          };
        }
      }

      // Return a properly structured error result
      return {
        isThreat: false,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }
);

/**
 * Actor for processing detected threats
 * Simplified to just pass through the detected threat without additional processing
 */
export const processThreatsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }): Promise<Threat> => {
    console.log(
      "[processThreatsActor] Passing through threat:",
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

    // Simply return the detected threat without any processing
    return input.context.detectedThreat;
  }
);

/**
 * Actor for composing actions based on detected threats
 * Enhanced to use AgentService for structured action recommendations
 */
export const composeActionsActor = fromPromise(
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
      // Initialize ActionCompositionAgent if not already initialized
      await actionCompositionAgent.initialize().catch((error) => {
        console.warn(
          "[composeActionsActor] Failed to initialize actionCompositionAgent:",
          error
        );
        // Continue execution - we'll use fallback if needed
      });

      // Get dependency graph data for context
      const dependencyGraph = DependencyGraphService.getDependencyGraph();
      const dependencyGraphString = JSON.stringify(dependencyGraph, null, 2);

      // Create the system prompt for action composition
      const systemPrompt =
        "You are a specialized security response coordinator for DeFi protocols. Your task is to recommend specific, actionable steps to mitigate security threats affecting blockchain protocols or tokens.";

      // Use the imported schema instead of defining it inline
      // Create the user prompt with the threat and dependency graph
      const prompt = `
      I need to respond to the following security threat:
      
      ${JSON.stringify(input.context.detectedThreat, null, 2)}
      
      Our project depends on these protocols and tokens:
      ${dependencyGraphString}
      
      Based on this threat and our dependencies, recommend specific actions that should be taken immediately.
      Focus on concrete, actionable steps that will protect our assets and mitigate the risk.
      
      For each action, return:
      1. actionType: Must be one of "swap", "withdraw", or "revoke"
      2. protocol: The name of the affected protocol
      3. token: The token symbol involved in the action
      4. description: A detailed explanation of what this action will do
      5. priority: How urgent this action is ("low", "medium", "high", "critical")
      6. params: A map of parameters needed (amounts, destinations, etc.)

      choose the best tool for the job. use multiple tools if needed.
      `;

      // Use generateObject method with the imported actionRecommendationSchema
      const result = await actionCompositionAgent.generateObject({
        prompt,
        schema: actionRecommendationSchema,
        systemPrompt,
        temperature: 0.2, // Low temperature for consistent, practical recommendations
      });

      console.log("[composeActionsActor] Action composition result:", result);

      // Handle empty actions result
      if (!result || !result.actions || result.actions.length === 0) {
        console.warn("[composeActionsActor] No actions generated for threat");
        return [];
      }

      // Transform the result into Action objects with the correct structure
      const actions: Action[] = result.actions.map((action) => ({
        type: action.actionType,
        protocol: action.protocol,
        token: action.token,
        params: action.params || {},
      }));

      return actions;
    } catch (error) {
      console.error("[composeActionsActor] Error composing actions:", error);

      // Fallback to using original actionComposer if agent-based approach fails
      try {
        console.warn("[composeActionsActor] Falling back to actionComposer");
        const fallbackActions = await actionComposer.composeActions(
          input.context.detectedThreat
        );

        if (fallbackActions && fallbackActions.length > 0) {
          return fallbackActions;
        }
      } catch (fallbackError) {
        console.error(
          "[composeActionsActor] Fallback also failed:",
          fallbackError
        );
      }

      // Return empty array if both approaches fail, allowing state machine to continue
      return [];
    }
  }
);

/**
 * Actor for executing composed actions
 * Enhanced to execute multiple actions with individual action tracking
 */
export const executeActionsActor = fromPromise(
  async ({ input }: { input: { context: HorusContext } }) => {
    console.log(
      "[executeActionsActor] Executing actions plan with",
      input.context.actionPlan?.length || 0,
      "actions:"
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

    // Log each action to be executed with an index
    input.context.actionPlan.forEach((action, index) => {
      console.log(
        `[executeActionsActor] Action ${index + 1}/${
          input.context.actionPlan.length
        }:`,
        `${action.type} on ${action.protocol} for ${action.token}`,
        action.params
      );
    });

    try {
      // Execute all actions at once via the actionExecutor service
      console.log("[executeActionsActor] Executing batch of actions...");
      const results = await actionExecutor.executeActions(
        input.context.actionPlan
      );

      // Log summary of execution results
      const successCount = results.filter((r) => r.status === "success").length;
      console.log(
        `[executeActionsActor] Execution complete: ${successCount}/${results.length} actions succeeded`
      );

      // Log individual results
      results.forEach((result, index) => {
        const status = result.status === "success" ? "✅" : "❌";
        console.log(
          `[executeActionsActor] ${status} Action ${index + 1} (${
            result.action.type
          }): ${
            result.status === "success"
              ? `Success, txHash: ${result.txHash}`
              : `Failed: ${result.error || "Unknown error"}`
          }`
        );
      });

      return results;
    } catch (error) {
      console.error("[executeActionsActor] Error executing actions:", error);

      // Return partial results with detailed error information for each action
      return input.context.actionPlan.map((action) => ({
        action,
        status: "failed" as const,
        txHash: "",
        error: error instanceof Error ? error.message : String(error),
        timestamp: Date.now(),
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
