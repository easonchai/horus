import { describe, expect, it } from "vitest";
import { createActor } from "xstate";
import { Signal } from "../src/models/types";
import { horusMachine } from "../src/state/machine";

describe("Horus State Machine", () => {
  it("should transition to evaluating state when receiving a signal", async () => {
    // Create and start the actor with initial context
    const actor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    actor.start();

    // Subscribe to state changes for debugging
    actor.subscribe((state) => {
      console.log(`State: ${state.value}`, state.context);
    });

    // Verify initial state is 'idle'
    expect(actor.getSnapshot().value).toBe("idle");
    expect(actor.getSnapshot().context.signals).toHaveLength(0);

    // Create a test signal
    const testSignal: Signal = {
      source: "twitter",
      content: "Test signal",
      timestamp: Date.now(),
    };

    // Send a signal to the machine
    actor.send({
      type: "SIGNAL_RECEIVED",
      signal: testSignal,
    });

    // Wait briefly for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Check current state and context
    const snapshot = actor.getSnapshot();
    console.log("Current state:", snapshot.value);

    // Verify the signal was added to the signals array
    expect(snapshot.context.signals).toHaveLength(1);
    expect(snapshot.context.signals[0]).toEqual(testSignal);

    // Manually transition back to idle
    actor.send({ type: "NO_THREAT_DETECTED" });

    // Wait briefly for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Verify we're back to idle
    const finalSnapshot = actor.getSnapshot();
    console.log("Final state:", finalSnapshot.value);
    expect(finalSnapshot.value).toBe("idle");
  });

  it("should clear current signal when transitioning back to idle", async () => {
    // Create and start the actor with initial context
    const actor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    actor.start();

    // Create a test signal
    const testSignal: Signal = {
      source: "twitter",
      content: "Test signal",
      timestamp: Date.now(),
    };

    // Use a promise to wait for the evaluating state
    const evaluatingPromise = new Promise<void>((resolve) => {
      const subscription = actor.subscribe((state) => {
        console.log(`State transition: ${state.value}`);

        // When we reach the evaluating state, check the context
        if (state.value === "evaluating") {
          expect(state.context.currentSignal).toEqual(testSignal);
          subscription.unsubscribe();
          resolve();
        }
      });
    });

    // Send a signal to the machine
    actor.send({
      type: "SIGNAL_RECEIVED",
      signal: testSignal,
    });

    // Wait for the evaluating state to be reached
    await evaluatingPromise;

    // Wait for the actor to process the signal evaluation
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Manually transition back to idle
    actor.send({ type: "NO_THREAT_DETECTED" });

    // Wait briefly for state to stabilize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Verify current signal is cleared but signals array still contains the signal
    const finalSnapshot = actor.getSnapshot();
    expect(finalSnapshot.value).toBe("idle");
    expect(finalSnapshot.context.currentSignal).toBeUndefined();
    expect(finalSnapshot.context.signals).toHaveLength(1);
    expect(finalSnapshot.context.signals[0]).toEqual(testSignal);
  });
});
