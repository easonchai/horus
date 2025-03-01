import { openai } from "@ai-sdk/openai";
import { ActionProvider, AgentKit, WalletProvider } from "@coinbase/agentkit";
import { generateObject, generateText } from "ai";
import * as dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

// Configuration options for AgentService
interface AgentServiceConfig {
  walletProvider: WalletProvider;
  actionProviders: ActionProvider<WalletProvider>[];
  modelName?: string;
  temperature?: number;
  systemMessage?: string;
}

/**
 * Options for generating structured data using a schema
 */
export interface GenerateObjectOptions<T extends z.ZodType> {
  /** The prompt to process */
  prompt: string;
  /** Zod schema defining the expected structure */
  schema: T;
  /** Optional override for the system prompt */
  systemPrompt?: string;
  /** Optional temperature parameter to control randomness */
  temperature?: number;
}

/**
 * Service for AI-powered agent interactions using Coinbase's AgentKit
 * Designed to support multiple instances with different action providers
 */
export class AgentService {
  private agentKit: AgentKit | null = null;
  private config: AgentServiceConfig;
  private defaultModelName = "gpt-4o";

  /**
   * Create a new AgentService
   * @param config Configuration for the service
   */
  constructor(config: AgentServiceConfig) {
    this.config = {
      ...config,
      actionProviders: config.actionProviders || [],
      modelName: config.modelName || this.defaultModelName,
      temperature: config.temperature || 0.2,
      systemMessage:
        config.systemMessage ||
        "You are an AI assistant analyzing blockchain security threats.",
    };

    // Validate configuration
    if (!process.env.OPENAI_API_KEY) {
      throw new Error("OPENAI_API_KEY environment variable is required");
    }
  }

  /**
   * Initialize the AgentKit instance with the wallet provider and action providers
   */
  async initialize(): Promise<void> {
    // Return if already initialized
    if (this.agentKit) return;

    try {
      // Initialize AgentKit with the provided configuration
      this.agentKit = await AgentKit.from({
        walletProvider: this.config.walletProvider,
        actionProviders: this.config.actionProviders,
      });

      console.log("AgentKit initialized successfully");
    } catch (error) {
      console.error("Failed to initialize AgentKit:", error);
      throw error;
    }
  }

  /**
   * Generate structured data using the specified schema
   * Uses Vercel AI SDK's generateObject function to ensure type safety
   * @param options Configuration options for generating structured data
   * @returns A structured object that conforms to the provided schema
   */
  async generateObject<T extends z.ZodType>(
    options: GenerateObjectOptions<T>
  ): Promise<z.infer<T>> {
    // Ensure we always have a valid model name
    const modelName = this.config.modelName || this.defaultModelName;

    try {
      // Use Vercel AI SDK's generateObject with the provided schema
      const result = await generateObject({
        model: openai(modelName),
        system: options.systemPrompt || this.config.systemMessage || "",
        prompt: options.prompt,
        schema: options.schema,
        temperature: options.temperature ?? this.config.temperature ?? 0.2,
      });

      console.log("[AgentService] Generated structured data:", result.object);
      return result.object;
    } catch (error) {
      console.error("[AgentService] Error generating structured data:", error);
      throw new Error(
        `Failed to generate structured data: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }

  /**
   * Generate a response for a given prompt using the configured model and tools
   * @param prompt The user prompt to process
   * @param systemPrompt Optional override for the system prompt
   */
  async generateResponse(
    prompt: string,
    systemPrompt?: string
  ): Promise<string> {
    if (!this.agentKit) {
      await this.initialize();
    }

    if (!this.agentKit) {
      throw new Error("AgentKit not initialized");
    }

    const actions = this.agentKit.getActions();
    // Ensure we always have a valid model name
    const modelName = this.config.modelName || this.defaultModelName;

    try {
      const { text } = await generateText({
        model: openai(modelName),
        system: systemPrompt || this.config.systemMessage || "",
        prompt: prompt,
        temperature: this.config.temperature || 0.2,
        tools: Object.fromEntries(
          actions.map((action) => [
            action.name,
            {
              name: action.name,
              description: action.description,
              parameters: action.schema,
              execute: (params) => action.invoke(params),
            },
          ])
        ),
      });

      return text;
    } catch (error) {
      console.error("Error generating response:", error);
      throw new Error(
        `Failed to generate response: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }

  /**
   * Get the initialized AgentKit instance
   */
  getAgentKit(): AgentKit | null {
    return this.agentKit;
  }
}
