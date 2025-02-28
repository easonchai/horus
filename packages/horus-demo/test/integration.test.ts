import { describe, expect, it } from "vitest";
import { createActor } from "xstate";
import { Signal } from "../src/models/types";
import { horusMachine } from "../src/state/machine";

describe("Horus Integration", () => {
  it("verifies basic signal handling and context updates", async () => {
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

    // Track states for verification
    const stateHistory: string[] = [];

    horusActor.subscribe((state) => {
      console.log(
        `State transition: ${state.value}`,
        JSON.stringify(state.context)
      );
      stateHistory.push(String(state.value));
    });

    // Create a test signal
    const testSignal: Signal = {
      source: "twitter",
      content: "Potential hack on Uniswap detected!",
      timestamp: Date.now(),
    };

    // STEP 1: Send signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: testSignal,
    });

    // Wait for state transition to evaluating and back to idle
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Verify the signal was added to context
    const finalContext = horusActor.getSnapshot().context;
    expect(finalContext.signals).toHaveLength(1);
    expect(finalContext.signals[0]).toEqual(testSignal);

    // Verify we visited the evaluating state
    expect(stateHistory).toContain("evaluating");

    // Verify we end up back in idle
    expect(horusActor.getSnapshot().value).toBe("idle");

    // Log the state history
    console.log("Complete state history:", stateHistory);
  });
});
