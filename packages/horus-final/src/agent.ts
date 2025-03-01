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
      Please analyze the following message for potential security threats to DeFi protocols:
      
      SOURCE: ${signal.source}
      CONTENT: ${signal.content}
      TIMESTAMP: ${new Date(signal.timestamp).toISOString()}
      
      Determine if this message indicates a security threat, what protocols might be affected,
      and what actions should be taken to mitigate any risks.
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
export const agent = new Agent();
