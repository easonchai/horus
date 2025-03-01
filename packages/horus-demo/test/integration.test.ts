import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createActor } from "xstate";
import { Signal } from "../src/models/types";
import { horusMachine } from "../src/state/machine";

describe("Horus Integration", () => {
  // Setup and cleanup for each test
  beforeEach(() => {
    // Use fake timers for better control of async operations
    vi.useFakeTimers();
  });

  afterEach(() => {
    // Restore timers and mocks after each test
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("verifies basic signal handling and context updates", async () => {
    console.log("Starting basic signal test");
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
    console.log("Initial state:", horusActor.getSnapshot().value);

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
    console.log("Sending signal to actor");
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: testSignal,
    });

    // Fast-forward time to allow all pending timers to execute
    // This will trigger all timers in one go
    console.log("Running all timers to complete state transitions");
    await vi.runAllTimersAsync();

    // Verify the signal was added to context
    const finalContext = horusActor.getSnapshot().context;
    console.log("Final state:", horusActor.getSnapshot().value);
    console.log("State history:", stateHistory);

    expect(finalContext.signals).toHaveLength(1);
    expect(finalContext.signals[0]).toEqual(testSignal);

    // Verify we visited the evaluating state
    expect(stateHistory).toContain("evaluating");

    // Verify we end up back in idle
    expect(horusActor.getSnapshot().value).toBe("idle");

    // Log the state history
    console.log("Complete state history:", stateHistory);
  });

  // Implement PATH 1 test for critical threat workflow
  it("PATH 1: should process critical threat through the entire workflow", async () => {
    // Create detailed log messages for debugging
    const log = (message: string, data?: unknown) => {
      console.log(
        `[CRITICAL-PATH-TEST] ${message}`,
        data ? JSON.stringify(data) : ""
      );
    };

    log("Initializing test for critical threat path");

    // Initialize our actor with initial context
    const horusActor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    log("Starting actor");
    horusActor.start();
    log("Initial state:", horusActor.getSnapshot().value);

    // Track states and transitions for verification
    const stateHistory: string[] = [];
    // Make sure we capture the initial state
    stateHistory.push(String(horusActor.getSnapshot().value));
    log("Added initial state to history:", horusActor.getSnapshot().value);

    horusActor.subscribe((snapshot) => {
      const stateValue = String(snapshot.value);
      stateHistory.push(stateValue);
      log(`State transition to: ${stateValue}`);
    });

    // Create a test signal with critical threat keywords and protocol mentions
    const criticalSignal: Signal = {
      source: "twitter",
      content:
        "CRITICAL vulnerability in Uniswap detected! All funds at risk. USDC token might be compromised.",
      timestamp: Date.now(),
    };

    log("Sending critical signal", criticalSignal);

    // Send signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: criticalSignal,
    });

    // Fast-forward time to run all current and future timers
    log("Fast-forwarding time to complete all state transitions");

    // Use runAllTimersAsync which automatically runs timers until there are none left
    await vi.runAllTimersAsync();

    // Check final state and context
    const finalState = horusActor.getSnapshot();
    const finalContext = finalState.context;

    log("Final state", { value: finalState.value, stateHistory });
    log("Final context summary", {
      signalsCount: finalContext.signals?.length || 0,
      threatDetected: !!finalContext.detectedThreat,
      threatSeverity: finalContext.detectedThreat?.severity,
      actionPlanCount: finalContext.actionPlan?.length || 0,
      executionResultsCount: finalContext.executionResults?.length || 0,
    });

    // Verify the signal was processed
    expect(finalContext.signals).toHaveLength(1);
    expect(finalContext.signals[0]).toEqual(criticalSignal);

    // Verify we went through the expected states
    log("State history for verification:", stateHistory);
    expect(stateHistory).toContain("idle");
    expect(stateHistory).toContain("evaluating");
    expect(stateHistory).toContain("processing");
    expect(stateHistory).toContain("composing");
    expect(stateHistory).toContain("executing");

    // We expect to reach "completed" state then transition back to "idle"
    expect(stateHistory).toContain("completed");

    // Verify the sequence of states is correct
    log("State history for sequence check:", stateHistory);
    let expectedSequenceFound = false;

    // Find the pattern: idle -> evaluating -> processing -> composing -> executing -> completed -> idle
    for (let i = 0; i < stateHistory.length - 6; i++) {
      if (
        stateHistory[i] === "idle" &&
        stateHistory[i + 1] === "evaluating" &&
        stateHistory[i + 2] === "processing" &&
        stateHistory[i + 3] === "composing" &&
        stateHistory[i + 4] === "executing" &&
        stateHistory[i + 5] === "completed" &&
        stateHistory[i + 6] === "idle"
      ) {
        expectedSequenceFound = true;
        break;
      }
    }

    log("Expected sequence found:", expectedSequenceFound);
    expect(expectedSequenceFound).toBe(true);

    // Verify we detected a threat
    expect(finalContext.detectedThreat).toBeDefined();
    if (finalContext.detectedThreat) {
      expect(finalContext.detectedThreat.severity).toBe("critical");
      expect(finalContext.detectedThreat.affectedTokens).toContain("USDC");
    }

    // We now expect to have at least one action in the action plan
    expect(finalContext.actionPlan.length).toBeGreaterThan(0);

    // Verify we have execution results
    expect(finalContext.executionResults.length).toBeGreaterThan(0);

    // Verify final state is idle (after completing the workflow)
    expect(finalState.value).toBe("idle");

    // Log the complete state history
    console.log("Complete state history:", stateHistory);
  });

  it("PATH 2: should evaluate non-threat signal and return to idle", async () => {
    // Create detailed log messages for debugging
    const log = (message: string, data?: unknown) => {
      console.log(
        `[NON-THREAT-TEST] ${message}`,
        data ? JSON.stringify(data) : ""
      );
    };

    log("Initializing test for non-threat path");

    // Initialize our actor with initial context
    const horusActor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    log("Starting actor");
    horusActor.start();
    log("Initial state:", horusActor.getSnapshot().value);

    // Make sure we capture the initial state
    const stateHistory: string[] = [String(horusActor.getSnapshot().value)];
    log("Added initial state to history:", horusActor.getSnapshot().value);

    // Track states and transitions for verification
    horusActor.subscribe((snapshot) => {
      const stateValue = String(snapshot.value);
      stateHistory.push(stateValue);
      log(`State transition to: ${stateValue}`);
    });

    // Create a non-threat test signal (no security keywords or protocol mentions)
    const nonThreatSignal: Signal = {
      source: "twitter",
      content:
        "Just released a new blog post about blockchain technology. Check it out!",
      timestamp: Date.now(),
    };

    log("Sending non-threat signal", nonThreatSignal);

    // Send signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: nonThreatSignal,
    });

    // Fast-forward time to run all current and future timers
    log("Fast-forwarding time to complete all state transitions");
    await vi.runAllTimersAsync();

    // Check final state and context
    const finalState = horusActor.getSnapshot();
    const finalContext = finalState.context;

    log("Final state", { value: finalState.value, stateHistory });
    log("Final context summary", {
      signalsCount: finalContext.signals?.length,
      currentSignal: finalContext.currentSignal,
      threatDetected: !!finalContext.detectedThreat,
      actionPlanCount: finalContext.actionPlan?.length,
      executionResultsCount: finalContext.executionResults?.length,
    });

    // Verify the signal was added to context
    expect(finalContext.signals).toHaveLength(1);
    expect(finalContext.signals[0]).toEqual(nonThreatSignal);

    // Verify we only visited the idle and evaluating states
    expect(stateHistory).toContain("idle");
    expect(stateHistory).toContain("evaluating");

    // Verify we did NOT visit processing or later states
    expect(stateHistory).not.toContain("processing");
    expect(stateHistory).not.toContain("composing");
    expect(stateHistory).not.toContain("executing");

    // Verify the sequence of states is correct (just idle -> evaluating -> idle)
    log("State history for sequence check:", stateHistory);
    let expectedSequenceFound = false;
    for (let i = 0; i < stateHistory.length - 2; i++) {
      if (
        stateHistory[i] === "idle" &&
        stateHistory[i + 1] === "evaluating" &&
        stateHistory[i + 2] === "idle"
      ) {
        expectedSequenceFound = true;
        break;
      }
    }

    log("Expected sequence found:", expectedSequenceFound);
    expect(expectedSequenceFound).toBe(true);

    // Verify no threat was detected
    expect(finalContext.detectedThreat).toBeUndefined();

    // Verify no actions were composed
    expect(finalContext.actionPlan).toEqual([]);

    // Verify no execution results
    expect(finalContext.executionResults).toEqual([]);

    // Verify final state is idle
    expect(finalState.value).toBe("idle");

    // Verify currentSignal was cleared
    expect(finalContext.currentSignal).toBeUndefined();

    // Log the complete state history
    console.log("Complete state history:", stateHistory);
  });

  // Add test for AgentKit integration with dependency token filtering
  it("PATH 3: should only process threats that affect dependency tokens", async () => {
    // Create detailed log messages for debugging
    const log = (message: string, data?: unknown) => {
      console.log(
        `[DEPENDENCY-TOKEN-TEST] ${message}`,
        data ? JSON.stringify(data) : ""
      );
    };

    log("Initializing test for dependency token filtering with AgentKit");

    // Initialize our actor with initial context
    const horusActor = createActor(horusMachine, {
      input: {
        signals: [],
        actionPlan: [],
        executionResults: [],
      },
    });

    // Start the actor
    log("Starting actor");
    horusActor.start();
    log("Initial state:", horusActor.getSnapshot().value);

    // Track states and transitions for verification
    const stateHistory: string[] = [];
    // Make sure we capture the initial state
    stateHistory.push(String(horusActor.getSnapshot().value));
    log("Added initial state to history:", horusActor.getSnapshot().value);

    horusActor.subscribe((snapshot) => {
      const stateValue = String(snapshot.value);
      stateHistory.push(stateValue);
      log(`State transition to: ${stateValue}`);
    });

    // Create a test signal with a threat but NOT mentioning any tokens in our dependency graph
    // This should be evaluated as NOT a relevant threat by AgentKit
    const irrelevantThreatSignal: Signal = {
      source: "twitter",
      content:
        "Vulnerability discovered in SomeUnrelatedProtocol! Funds at risk for RandomToken.",
      timestamp: Date.now(),
    };

    log("Sending irrelevant threat signal", irrelevantThreatSignal);

    // Send signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: irrelevantThreatSignal,
    });

    // Fast-forward time to run all current and future timers
    log("Fast-forwarding time to complete all state transitions");
    await vi.runAllTimersAsync();

    // Check first state and context
    const firstState = horusActor.getSnapshot();
    const firstContext = firstState.context;

    log("First completed state", { value: firstState.value, stateHistory });
    log("First context summary", {
      signalsCount: firstContext.signals?.length || 0,
      threatDetected: !!firstContext.detectedThreat,
    });

    // Verify we didn't progress past evaluating for irrelevant threat
    let irrelevantSequenceFound = false;
    for (let i = 0; i < stateHistory.length - 2; i++) {
      if (
        stateHistory[i] === "idle" &&
        stateHistory[i + 1] === "evaluating" &&
        stateHistory[i + 2] === "idle"
      ) {
        irrelevantSequenceFound = true;
        break;
      }
    }

    expect(irrelevantSequenceFound).toBe(true);
    log("Irrelevant threat correctly ignored, now testing relevant threat");

    // Reset state history for next test
    stateHistory.length = 0;
    stateHistory.push(String(horusActor.getSnapshot().value));

    // Create a test signal with a threat mentioning tokens in our dependency graph
    // This should be evaluated as a relevant threat by AgentKit
    const relevantThreatSignal: Signal = {
      source: "twitter",
      content:
        "Vulnerability discovered in Uniswap! All funds at risk. USDC and ETH may be affected.",
      timestamp: Date.now(),
    };

    log("Sending relevant threat signal", relevantThreatSignal);

    // Send signal to the actor
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal: relevantThreatSignal,
    });

    // Fast-forward time to run all current and future timers
    log("Fast-forwarding time to complete all state transitions");
    await vi.runAllTimersAsync();

    // Check final state and context
    const finalState = horusActor.getSnapshot();
    const finalContext = finalState.context;

    log("Final state after relevant threat", {
      value: finalState.value,
      stateHistory,
    });
    log("Final context summary", {
      signalsCount: finalContext.signals?.length || 0,
      threatDetected: !!finalContext.detectedThreat,
      threatSeverity: finalContext.detectedThreat?.severity,
      actionPlanCount: finalContext.actionPlan?.length || 0,
      executionResultsCount: finalContext.executionResults?.length || 0,
    });

    // Verify the signals were processed
    expect(finalContext.signals).toHaveLength(2);
    expect(finalContext.signals).toContainEqual(relevantThreatSignal);

    // Verify we went through the expected states for the relevant threat
    expect(stateHistory).toContain("idle");
    expect(stateHistory).toContain("evaluating");
    expect(stateHistory).toContain("processing");

    // Verify the threat was detected for the relevant threat
    expect(finalContext.detectedThreat).toBeDefined();
    if (finalContext.detectedThreat) {
      expect(finalContext.detectedThreat.affectedTokens).toEqual(
        expect.arrayContaining(["USDC"]) // Should contain USDC
      );
    }

    // Log the complete state history
    log("Complete state history:", stateHistory);
  });
});
