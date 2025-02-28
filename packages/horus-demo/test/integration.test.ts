import { describe, expect, it } from "vitest";
import { createActor } from "xstate";
import { Action, Signal, Threat } from "../src/models/types";
import { horusMachine } from "../src/state/machine";

// Create a mock threat for testing
const mockThreat: Threat = {
  description: "Potential security threat",
  affectedProtocols: ["uniswap"],
  affectedTokens: ["ETH"],
  chain: "ethereum",
  severity: "high",
};

// Create a mock action plan
const mockActionPlan: Action[] = [
  {
    type: "swap",
    protocol: "uniswap",
    token: "ETH",
    params: {
      fromToken: "ETH",
      toToken: "USDC",
      amount: "1.0",
    },
  },
];

// Create mock execution results
const mockExecutionResults = [
  {
    success: true,
    txHash: "0x123456789abcdef",
    action: mockActionPlan[0],
  },
];

describe("Horus Integration", () => {
  it("should process a security threat through all states to completion", async () => {
    // Initialize our actor with initial context
    const horusActor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    horusActor.start();

    // Set up state tracking
    const stateHistory: string[] = [];
    horusActor.subscribe((state) => {
      console.log(`State transition: ${state.value}`, state.context);
      stateHistory.push(String(state.value));
    });

    // Create a test signal
    const testSignal: Signal = {
      source: "twitter",
      content: "Potential hack on Uniswap detected!",
      timestamp: Date.now(),
    };

    // Send the signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: testSignal,
    });

    // Wait for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Manually trigger threat detection
    horusActor.send({
      type: "THREAT_DETECTED",
      threat: mockThreat,
    });

    // Wait for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Manually trigger action composition completion
    horusActor.send({
      type: "ACTIONS_CREATED",
      actions: mockActionPlan,
    });

    // Wait for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Manually trigger action execution completion
    horusActor.send({
      type: "EXECUTION_COMPLETED",
      results: mockExecutionResults,
    });

    // Wait for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Verify that we reached the completed state
    const finalSnapshot = horusActor.getSnapshot();
    console.log("Final state:", finalSnapshot.value);
    expect(finalSnapshot.value).toBe("completed");

    // Verify that context was updated correctly
    expect(finalSnapshot.context.signals).toContain(testSignal);
    expect(finalSnapshot.context.detectedThreat).toEqual(mockThreat);
    expect(finalSnapshot.context.actionPlan).toEqual(mockActionPlan);
    expect(finalSnapshot.context.executionResults).toEqual(
      mockExecutionResults
    );

    // Verify that all states were visited in the correct order
    expect(stateHistory).toContain("idle");
    expect(stateHistory).toContain("evaluating");
    expect(stateHistory).toContain("processingThreat");
    expect(stateHistory).toContain("composingActions");
    expect(stateHistory).toContain("executingActions");
    expect(stateHistory).toContain("completed");
  }, 10000); // Longer timeout to ensure all state transitions complete
});
