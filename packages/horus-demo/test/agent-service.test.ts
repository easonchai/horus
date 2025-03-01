import "reflect-metadata";

import { ViemWalletProvider, walletActionProvider } from "@coinbase/agentkit";
import { describe, it } from "vitest";
import { evaluateTweetsActionProvider } from "../src/providers/tweet-evaluation.provider";
import { AgentService } from "../src/services/agent-service";
import { WalletService } from "../src/services/wallet-service";

/**
 * Example setup function demonstrating how to use the AgentService
 */
async function testSetup() {
  const wallet = new WalletService();
  const walletClient = wallet.getWalletClient();

  if (!walletClient) {
    throw new Error("Wallet client not initialized");
  }

  const walletProvider = new ViemWalletProvider(walletClient);

  // Create agent service with specific action providers
  const agentService = new AgentService({
    walletProvider,
    actionProviders: [walletActionProvider(), evaluateTweetsActionProvider()],
    systemMessage: "be very very brief",
  });

  await agentService.initialize();

  const response = await agentService.generateResponse(
    "list the tools you have available"
  );

  console.log("prompt text", response);
  console.log("Agent setup completed successfully");
  return response;
}

describe("AgentService Tests", () => {
  it("should run the test setup function", async () => {
    const message = await testSetup();
    console.log("message", message);
  });
});
