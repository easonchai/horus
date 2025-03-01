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

interface AgentConfig {
  systemMessage?: string;
  modelName?: string;
  temperature?: number;
}

export class Agent {
  private agentKit;
  private config: AgentConfig;
  private defaultModelName = "gpt-4o";

  constructor(config: AgentConfig = {}) {
    this.config = config;
    this.agentKit = agentKit;
  }

  /**
   * Initialize the agent by ensuring AgentKit is loaded
   */
  async initialize(): Promise<void> {
    if (!this.agentKit) {
      this.agentKit = await getAgent();
    }
  }

  /**
   * Process a signal to determine if it represents a security threat
   * @param signal The signal to process
   * @returns Analysis result including threat assessment
   */
  async processSignal(signal: Signal, systemPrompt?: string): Promise<any> {
    await this.initialize();

    const prompt = `
      Please analyze the following message for potential security threats to DeFi protocols:
      
      SOURCE: ${signal.source}
      CONTENT: ${signal.content}
      TIMESTAMP: ${new Date(signal.timestamp).toISOString()}
      
      Determine if this message indicates a security threat, what protocols might be affected,
      and what actions should be taken to mitigate any risks.
    `;

    return this.generateResponse(prompt, systemPrompt);
  }

  /**
   * Generate a response using AI with tools
   * @param prompt The prompt to send to the AI
   * @param systemPrompt Optional system prompt override
   * @returns The generated response
   */
  private async generateResponse(
    prompt: string,
    systemPrompt?: string
  ): Promise<any> {
    await this.initialize();

    // Get actions from agentKit
    const actions = this.agentKit?.getActions() || [];

    // Ensure we always have a valid model name
    const modelName = this.config.modelName || this.defaultModelName;

    try {
      const { text } = await generateText({
        model: openai(modelName),
        maxSteps: 25,
        system: systemPrompt || this.config.systemMessage || "",
        prompt: prompt,
        temperature: this.config.temperature || 0.2,
        tools: Object.fromEntries([
          ...actions.map((action) => [
            action.name,
            {
              name: action.name,
              description: action.description,
              parameters: action.schema,
              execute: (params: any) => action.invoke(params),
            },
          ]),
        ]),
      });

      return { text };
    } catch (error) {
      console.error("Error generating response:", error);
      throw error;
    }
  }
}

// Create and export a default agent instance
export const agent = new Agent();
