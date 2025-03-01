/**
 * Agent Implementation
 *
 * This file creates an Agent class that uses AgentKit and implements
 * text generation capabilities with tools for processing signals and
 * executing actions in DeFi protocols.
 */

import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { agentKit, getAgent } from "./agentKit";
import dependencyGraphData from "./data/dependency_graph.json";
import protocolsData from "./data/protocols.json";
import { Signal } from "./types";
import { getLogger } from "./utils/logger";

// Initialize logger for this component
const logger = getLogger("Agent");

/**
 * Configuration interface for the Agent
 *
 * @interface AgentConfig
 * @property {string} [systemMessage] - Optional system message to guide the AI's behavior
 * @property {string} [modelName] - Optional model name to use for text generation
 * @property {number} [temperature] - Optional temperature setting for controlling randomness
 */
interface AgentConfig {
  systemMessage?: string;
  modelName?: string;
  temperature?: number;
}

/**
 * Agent class for AI-powered DeFi security monitoring and response
 *
 * The Agent uses AgentKit to process signals from various sources,
 * analyze them for security threats, and recommend or execute
 * appropriate actions to protect user assets.
 */
export class Agent {
  private agentKit;
  private config: AgentConfig;
  private defaultModelName = "gpt-4o";

  /**
   * Creates a new Agent instance with optional configuration
   *
   * @param {AgentConfig} config - Optional configuration for the agent
   */
  constructor(config: AgentConfig = {}) {
    this.config = config;
    this.agentKit = agentKit;
    logger.info("Agent created with config:", config);
  }

  /**
   * Initialize the agent by ensuring AgentKit is loaded
   * Uses lazy initialization pattern to load AgentKit only when needed
   *
   * @returns {Promise<void>} Promise that resolves when initialization is complete
   */
  async initialize(): Promise<void> {
    if (!this.agentKit) {
      logger.debug("AgentKit not initialized, initializing now");
      this.agentKit = await getAgent();
      logger.info("AgentKit initialized successfully");
    }
  }

  /**
   * Process a signal to determine if it represents a security threat
   * Analyzes the signal content and provides a threat assessment with recommended actions
   *
   * @param {Signal} signal - The signal to process
   * @param {string} [systemPrompt] - Optional system prompt to override default behavior
   * @returns {Promise<any>} Analysis result including threat assessment
   */
  async processSignal(signal: Signal, systemPrompt?: string): Promise<any> {
    logger.info(`Processing signal from source: ${signal.source}`);
    logger.debug(
      `Signal timestamp: ${new Date(signal.timestamp).toISOString()}`
    );

    await this.initialize();

    const prompt = `
      Analyze the following signal for potential security threats to DeFi protocols:

      ## SIGNAL DETAILS
      SOURCE: ${signal.source}
      CONTENT: ${signal.content}
      TIMESTAMP: ${new Date(signal.timestamp).toISOString()}

      ## DEPENDENCY GRAPH
      ${JSON.stringify(dependencyGraphData, null, 2)}

      ## PROTOCOLS
      ${JSON.stringify(protocolsData, null, 2)}

      ## YOUR TASK
      1. Analyze this signal to determine if it represents a legitimate security threat to any protocols or tokens in the dependency graph
      2. If a threat is detected:
        - Identify which specific protocol or token is compromised
        - Determine which positions in the dependency graph are exposed to this threat
        - Outline the exact sequence of actions needed to protect these positions
        - Execute the necessary tool calls (swap/revoke/withdraw) in the correct order
      3. If no threat is detected or if no exposure exists in the dependency graph:
        - Explain why no action is needed
        - Take no further action

      Provide your analysis step-by-step and execute any necessary protective actions using the available tools.
    `;

    logger.debug("Generated signal analysis prompt");

    try {
      const response = await this.generateResponse(prompt, systemPrompt);
      logger.info("Signal processing completed successfully");
      return response;
    } catch (error) {
      logger.error("Error processing signal:", error);
      throw error;
    }
  }

  /**
   * Generate a response using AI with tools
   * This is the core method that utilizes the AI to generate responses
   * and allows the AI to use tools from AgentKit when needed
   *
   * @param {string} prompt - The prompt to send to the AI
   * @param {string} [systemPrompt] - Optional system prompt override
   * @returns {Promise<any>} The generated response
   * @private
   */
  private async generateResponse(
    prompt: string,
    systemPrompt?: string
  ): Promise<any> {
    await this.initialize();

    // Get actions from agentKit
    const actions = this.agentKit?.getActions() || [];
    logger.debug(`Loaded ${actions.length} available actions from AgentKit`);

    // Ensure we always have a valid model name
    const modelName = this.config.modelName || this.defaultModelName;
    logger.debug(`Using model: ${modelName}`);

    // If a system prompt was provided, use it; otherwise use the configured one
    const finalSystemPrompt = systemPrompt || this.config.systemMessage || "";
    if (finalSystemPrompt) {
      logger.debug("Using custom system prompt");
    }

    try {
      logger.info("Generating AI response with tools");

      const toolsObject = Object.fromEntries([
        ...actions.map((action) => [
          action.name,
          {
            name: action.name,
            description: action.description,
            parameters: action.schema,
            execute: (params: any) => {
              logger.info(`Executing tool: ${action.name}`);
              logger.debug(`Tool parameters:`, params);
              return action.invoke(params);
            },
          },
        ]),
      ]);

      logger.debug(
        `Configured ${Object.keys(toolsObject).length} tools for AI`
      );

      const { text } = await generateText({
        model: openai(modelName),
        maxSteps: 25,
        system: finalSystemPrompt,
        prompt: prompt,
        temperature: this.config.temperature || 0.2,
        tools: toolsObject,
      });

      logger.info("AI response generated successfully");
      return { text };
    } catch (error) {
      logger.error("Error generating response:", error);
      throw error;
    }
  }

  /**
   * Create a custom alert message for security threats
   *
   * @param {string} message - The alert message
   * @param {'low'|'medium'|'high'|'critical'} severity - The alert severity
   * @returns {string} Formatted alert message
   */
  createAlert(
    message: string,
    severity: "low" | "medium" | "high" | "critical"
  ): string {
    logger.warn(`Creating security alert with severity: ${severity}`);

    const timestamp = new Date().toISOString();
    const severitySymbol =
      severity === "critical"
        ? "🚨"
        : severity === "high"
        ? "⚠️"
        : severity === "medium"
        ? "⚠"
        : "ℹ️";

    const formattedAlert = `
      ${severitySymbol} SECURITY ALERT: ${severity.toUpperCase()} ${severitySymbol}

      ${message}

      Severity: ${severity}
      Time: ${timestamp}

      Please take appropriate action immediately.
    `;

    logger.debug("Alert created successfully");
    return formattedAlert;
  }
}

// Create and export a default agent instance
logger.info("Creating default Agent instance");
export const agent = new Agent({
  systemMessage: `
  You are Horus, an advanced AI security agent for DeFi protocols. Your primary function is to monitor signals (such as tweets) for potential security threats to blockchain protocols and automatically execute protective actions when necessary.

  ## YOUR CORE RESPONSIBILITIES

  1. DETECT THREATS: Analyze incoming signals (tweets, alerts) to identify security threats to DeFi protocols
  2. EVALUATE EXPOSURE: Determine if any positions in your dependency graph are exposed to the compromised protocol/token
  3. TAKE ACTION: If exposure exists, execute the appropriate sequence of transactions to protect assets
  4. MAINTAIN SAFETY: Take no action if there is no confirmed threat or exposure

  ## HOW TO ANALYZE SIGNALS

  For each incoming signal (tweet, alert message):
  - Look for keywords indicating security threats: "vulnerability", "exploit", "hack", "attack", "compromised", "drained", "emergency", "alert", "security incident"
  - Extract the affected protocol or token name mentioned in the signal
  - Assess the severity level (critical, high, medium, low)
  - Verify if the affected protocol or token exists in your dependency graph
  - Ignore signals that don't contain concrete security threats

  ## UNDERSTANDING THE DEPENDENCY GRAPH

  The dependency graph represents how tokens and protocols are interconnected:
  - "derivativeSymbol": The token symbol of the derivative position
  - "chainId": The blockchain network ID where the token exists
  - "protocol": The protocol that created this derivative (e.g., UniswapV3, Beefy)
  - "underlyings": The tokens or positions that this derivative depends on
  - "exitFunctions": Functions that can be called to exit from this position
  - "swapFunctions": Functions that can be called to swap between tokens

  ## DETERMINING EXPOSURE TO SECURITY THREATS

  When a protocol is compromised:
  1. Identify the specific token symbol from the compromised protocol
  2. Trace all positions in the dependency graph that directly or indirectly depend on this token
  3. A position is exposed if:
     - It directly contains the compromised token
     - It contains a derivative position that depends on the compromised token
     - It is provided as liquidity to the compromised protocol

  ## TAKING PROTECTIVE ACTIONS

  Based on exposure analysis, execute the appropriate sequence of protective actions:

  1. For direct exposure to compromised token:
     - Use swapFunctions to convert to a safe alternative token
     - Prioritize stablecoins (USDC, USDT) if available as swap targets

  2. For exposure through liquidity positions (e.g., Uniswap V3):
     - First call decreaseLiquidity to remove liquidity from the pool
     - Then call collect to claim the underlying tokens
     - Finally swap any compromised tokens using swapFunctions

  3. For exposure through yield positions (e.g., Beefy vaults):
     - Call withdraw to exit the vault position
     - Then handle the underlying tokens appropriately

  ## EXECUTION ORDER

  For complex positions with multiple layers of dependencies:
  1. Always exit from the outermost layer first (the derivative position)
  2. Work your way down to the underlying tokens
  3. For each underlying token that is exposed, determine if it needs to be swapped
  4. Execute multiple tool calls in sequence when necessary to complete the full exit path

  ## TOOLS AT YOUR DISPOSAL

  You have three main tools available:
  - swap: Convert one token to another through available DEX routes
  - revoke: Remove approvals from compromised contracts
  - withdraw: Exit positions from protocols like liquidity pools or yield vaults

  ## ACTION RESTRAINT

  Only take action when:
  - The signal clearly indicates a security threat
  - The threat affects a protocol or token in your dependency graph
  - There's confirmed exposure to the compromised entity

  If any of these conditions are not met, do not execute any transactions.

  ## EXAMPLE THREAT SCENARIOS

  1. "ALERT: Critical vulnerability found in Uniswap V3 contract. All funds at risk of being drained."
     - This affects Uniswap V3 positions in the dependency graph
     - Look for any positions with protocol "UniswapV3"
     - Execute the exit functions for those positions

  2. "ALERT: USDC depegging event in progress. Smart contract vulnerability detected."
     - This affects USDC token directly
     - Look for any positions containing USDC or derivatives of USDC
     - Swap USDC to safer alternatives using swapFunctions
     - Exit from positions dependent on USDC

  Remember that your primary mission is to protect user assets from security threats while avoiding unnecessary actions for non-threats. Be decisive when real threats emerge and take no action when the signal doesn't indicate a legitimate security concern.
  `,
});
