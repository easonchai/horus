import "reflect-metadata";
import { describe, expect, it, vi } from "vitest";

// Mock dependencies
vi.mock("../src/services/agent-service", () => {
  return {
    AgentService: vi.fn().mockImplementation(() => {
      return {
        initialize: vi.fn().mockResolvedValue(undefined),
        generateObject: vi.fn().mockResolvedValue({
          isThreat: true,
          threatDetails: {
            description: "Mock threat for testing",
            affectedProtocols: ["uniswap"],
            affectedTokens: ["ETH", "USDC"],
            chain: "ethereum",
            severity: "high",
          },
        }),
        config: {
          actionProviders: [],
          modelName: "test-model",
          temperature: 0.1,
        },
      };
    }),
  };
});

vi.mock("../src/services/action-composer", () => {
  return {
    ActionComposer: vi.fn().mockImplementation(() => {
      return {
        composeActions: vi.fn().mockResolvedValue([]),
      };
    }),
  };
});

vi.mock("../src/services/wallet-service", () => {
  return {
    WalletService: vi.fn().mockImplementation(() => {
      return {
        initialize: vi.fn().mockResolvedValue(undefined),
        walletProvider: {
          getAddress: vi.fn().mockResolvedValue("0x123"),
          getChainId: vi.fn().mockResolvedValue(1),
        },
      };
    }),
  };
});

describe("Horus State Machine", () => {
  it("should pass a basic test", () => {
    expect(true).toBe(true);
  });
});
