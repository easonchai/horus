// This will create a new AgentKit agent using AI SDK, our wallet, AgentKit and our ActionProviders.
// We will use the agent to process signals and execute actions.
/**
 * Agent Usage Documentation
 *
 * This documentation provides an overview of how to use the AgentKit agent
 * created in this module. The agent is designed to process signals and execute
 * actions in the context of decentralized finance (DeFi) protocols.
 *
 * ## Getting Started
 *
 * To use the agent, you need to follow these steps:
 *
 * 1. **Initialize the Agent**:
 *    Call the `getAgent()` function to retrieve the AgentKit instance. This function
 *    will create a new instance if one does not already exist.
 *
 *    ```typescript
 *    import { getAgent } from './agentKit';
 *
 *    async function main() {
 *      const agent = await getAgent();
 *      // Now you can use the agent instance
 *    }
 *    ```
 *
 * 2. **Process Signals**:
 *    Once you have the agent instance, you can use it to process signals.
 *    The agent will analyze the signals and determine if there are any security threats.
 *
 *    ```typescript
 *    const signal = {
 *      content: "Example tweet content to analyze for threats."
 *    };
 *
 *    const result = await agent.processSignal(signal);
 *    console.log("Signal analysis result:", result);
 *    ```
 *
 * 3. **Execute Actions**:
 *    Based on the analysis, you can execute actions recommended by the agent.
 *    The actions will be tailored to mitigate any identified threats.
 *
 *    ```typescript
 *    const actions = await agent.getRecommendedActions(signal);
 *    for (const action of actions) {
 *      await agent.executeAction(action);
 *    }
 *    ```
 *
 * ## Error Handling
 *
 * Ensure to handle errors gracefully when interacting with the agent.
 * The agent may throw errors if the wallet provider is not initialized or if
 * there are issues processing signals or executing actions.
 *
 * ```typescript
 * try {
 *   const agent = await getAgent();
 *   // Proceed with processing signals and executing actions
 * } catch (error) {
 *   console.error("Error interacting with the agent:", error);
 * }
 * ```
 *
 * ## Conclusion
 *
 * This agent provides a powerful interface for analyzing security threats
 * in the DeFi space. By following the steps outlined above, you can effectively
 * utilize the agent to enhance your security posture.
 */

import { AgentKit, ViemWalletProvider } from "@coinbase/agentkit";
import { Wallet } from "./wallet";

// Cache the AgentKit instance
let cachedAgentKit: AgentKit | null = null;

/**
 * Gets the existing AgentKit instance or creates a new one
 * @returns Promise resolving to an AgentKit instance
 */
export async function getAgent(): Promise<AgentKit> {
  // Return cached instance if it exists
  if (cachedAgentKit) {
    return cachedAgentKit;
  }

  // Otherwise create a new instance
  const wallet = new Wallet();
  const walletClient = wallet.getWalletClient();
  const walletProvider = walletClient
    ? new ViemWalletProvider(walletClient)
    : undefined;

  if (!walletProvider) {
    throw new Error("Failed to initialize wallet provider");
  }

  // Create and cache the AgentKit instance
  cachedAgentKit = await AgentKit.from({
    walletProvider,
    // TODO: Add all of the agent providers here
    actionProviders: [],
  });

  return cachedAgentKit;
}

// Export the function to get/create agent
export { cachedAgentKit as agentKit };
