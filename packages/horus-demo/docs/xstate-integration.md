# XState Integration in Horus

This document details how Horus integrates with XState to create a robust state machine-driven architecture with comprehensive error handling.

## Overview

Horus uses XState v5 to coordinate the workflow of monitoring signals, evaluating threats, and taking protective actions. The state machine architecture provides:

1. Clear visualization of application flow
2. Predictable state transitions
3. Centralized error handling
4. Type safety through TypeScript integration

## State Machine Design

The Horus state machine includes these primary states:

- **idle**: Waiting for security signals
- **evaluating**: Analyzing signals for threats
- **processing**: Determining affected protocols and tokens
- **composing**: Creating an action plan
- **executing**: Performing on-chain transactions
- **completed**: Successfully executed actions
- **failed**: Error handling & recovery

## Actor Pattern Implementation

Horus uses the XState actor pattern to handle asynchronous operations. Each major step in the workflow is implemented as an actor:

```typescript
// Actor for evaluating signals
const evaluateSignalsActor = fromPromise(
  async ({ input }): Promise<SignalEvaluationResult> => {
    // Implementation...
  }
);

// Actor for processing threats
const processThreatsActor = fromPromise(async ({ input }): Promise<Threat> => {
  // Implementation...
});

// Actor for composing actions
const composeActionsActor = fromPromise(
  async ({ input }): Promise<Action[]> => {
    // Implementation...
  }
);

// Actor for executing actions
const executeActionsActor = fromPromise(async ({ input }) => {
  // Implementation...
});

// Export the actors for use in the machine
export const actors = {
  evaluateSignals: evaluateSignalsActor,
  processThreats: processThreatsActor,
  composeActions: composeActionsActor,
  executeActions: executeActionsActor,
};
```

## Robust Error Handling

Each actor implements multiple layers of error handling:

### 1. Input Validation

Before processing begins, inputs are validated with helpful error messages:

```typescript
// Input validation with helpful error message
if (!input.context.currentSignal) {
  const error = new Error("No signal to evaluate");
  console.error(
    "[evaluateSignalsActor] Input validation failed:",
    error.message
  );
  throw error;
}
```

### 2. Structured Error Handling

Errors are handled in a structured way that maintains the state machine's flow:

```typescript
try {
  const result = await signalEvaluator.evaluateSignal(
    input.context.currentSignal
  );
  return result;
} catch (error) {
  // Enhanced error logging
  console.error("[evaluateSignalsActor] Error evaluating signal:", error);

  // Return a properly structured error result instead of throwing
  return {
    isThreat: false,
    error: error instanceof Error ? error : new Error(String(error)),
  };
}
```

### 3. Edge Case Handling

Edge cases are proactively identified and handled:

```typescript
// Handle edge case where isThreat is true but threat is undefined
if (result.isThreat && !result.threat) {
  console.warn(
    "[evaluateSignalsActor] Threat flagged but no threat details provided"
  );
  // Create a minimal threat object to prevent downstream errors
  return {
    isThreat: true,
    threat: {
      description: `Potential unnamed threat detected: ${input.context.currentSignal.content}`,
      affectedProtocols: [],
      affectedTokens: ["unknown"],
      chain: "ethereum",
      severity: "medium",
    },
  };
}
```

### 4. Fallback Mechanisms

When operations fail, actors provide sensible fallbacks instead of crashing:

```typescript
// In case of error, return the original threat rather than failing completely
console.warn(
  "[processThreatsActor] Returning original threat due to processing error"
);
return input.context.detectedThreat;
```

## State Machine Guards

The machine uses guards to determine state transitions based on actor output:

```typescript
guards: {
  isThreat: ({ event }) => {
    console.log("isThreat guard check with event:", event);
    // @ts-expect-error - Actor events in onDone have 'output' property
    return Boolean(event.output?.isThreat) && Boolean(event.output?.threat);
  },
  isNotThreat: ({ event }) => {
    console.log("isNotThreat guard check with event:", event);
    // @ts-expect-error - Actor events in onDone have 'output' property
    return event.output?.isThreat === false;
  },
  hasError: ({ event }) => {
    console.log("hasError guard check with event:", event);
    // @ts-expect-error - Actor events in onDone have 'output' property
    return Boolean(event.output?.error);
  }
},
```

## Error State Transitions

The machine includes dedicated transitions for error handling:

```typescript
evaluating: {
  invoke: {
    src: "evaluateSignals",
    input: ({ context }) => ({ context }),
    onDone: [
      {
        target: "processing",
        guard: { type: "isThreat" },
        // ...
      },
      {
        target: "failed",
        guard: { type: "hasError" },
        actions: assign({
          error: ({ event }) => {
            console.error("Signal evaluation failed with error:", event.output.error);
            return event.output.error;
          }
        }),
      },
      {
        target: "idle",
        guard: { type: "isNotThreat" },
        // ...
      },
    ],
    onError: {
      target: "failed",
      // ...
    },
  },
}
```

## Type Safety

The entire state machine is strongly typed with TypeScript:

```typescript
// Define types for context and events
export interface HorusContext {
  signals: Signal[];
  currentSignal?: Signal;
  detectedThreat?: Threat;
  actionPlan: Action[];
  executionResults: { success: boolean; txHash: string; action: Action }[];
  error?: Error;
}

export type HorusEvent =
  | { type: "SIGNAL_RECEIVED"; signal: Signal }
  | { type: "EVALUATE_SIGNALS" }
  | { type: "THREAT_DETECTED"; threat: Threat }
  | { type: "NO_THREAT_DETECTED" }
  | { type: "ACTIONS_CREATED"; actions: Action[] }
  | {
      type: "EXECUTION_COMPLETED";
      results: { success: boolean; txHash: string; action: Action }[];
    }
  | { type: "ERROR"; error: Error };

// Set up the machine with types
export const horusMachine = setup({
  types: {
    context: {} as HorusContext,
    events: {} as HorusEvent,
    input: {} as HorusContext,
    output: {} as Record<string, unknown>,
  },
  // ...
});
```

## Best Practices for XState Integration

When working with the Horus state machine:

1. **Actor Implementation**:

   - Always return properly typed results from actors
   - Include detailed error information in all actor responses
   - Use structured logging with actor name prefixes

2. **Error Handling**:

   - Add fallback mechanisms for all critical operations
   - Use the `error` property in return types rather than throwing
   - Ensure error states have clear paths back to normal operation

3. **Type Safety**:
   - Keep type definitions centralized in `models/types.ts`
   - Use explicit type annotations for actor return values
   - Use type assertions strategically for XState-specific patterns
