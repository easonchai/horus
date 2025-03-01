import { ViemWalletProvider, WalletProvider } from "@coinbase/agentkit";
import { fromPromise } from "xstate";
import { Action, SignalEvaluationResult, Threat } from "../models/types";
import { evaluateTweetsActionProvider } from "../providers/tweet-evaluation.provider";
import { threatAnalysisSchema } from "../schemas/threat-analysis.schema";
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

// Create action composer and executor services
const actionComposer = new ActionComposer();
const actionExecutor = new ActionExecutor();

/**
 * Actor for evaluating signals to detect threats
 * Uses AgentService with AgentKit integration and structured data from generateObject
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
 * Simplified since we now get structured data from evaluateSignalsActor
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
      // The threat is already structured with details from evaluateSignalsActor
      // So we just need to validate and possibly enhance it

      // Check if the threat has all required fields
      const threat = input.context.detectedThreat;

      // Ensure affectedProtocols is an array
      if (!Array.isArray(threat.affectedProtocols)) {
        threat.affectedProtocols = [];
      }

      // Ensure affectedTokens is an array
      if (!Array.isArray(threat.affectedTokens)) {
        threat.affectedTokens = [];
      }

      // Ensure we have a valid severity
      if (!["low", "medium", "high", "critical"].includes(threat.severity)) {
        threat.severity = "medium"; // Default to medium if invalid
      }

      // If we have analysisText, we can use it to augment the threat info if needed
      if (input.context.analysisText) {
        console.log(
          "[processThreatsActor] Additional analysis text available:",
          input.context.analysisText.substring(0, 100) + "..."
        );
      }

      console.log("[processThreatsActor] Processed threat:", threat);
      return threat;
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
