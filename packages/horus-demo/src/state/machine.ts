import { assign, setup } from "xstate";
import { actors } from "./actors";
import { HorusContext, HorusEvent } from "./types";

const initialContext: HorusContext = {
  signals: [],
  actionPlan: [],
  executionResults: [],
};

// The machine definition using XState v5 setup pattern
export const horusMachine = setup({
  types: {
    context: {} as HorusContext,
    events: {} as HorusEvent,
    input: {} as HorusContext,
    output: {} as Record<string, unknown>,
  },
  actions: {
    assignSignal: assign({
      signals: ({ context, event }) => {
        if (event.type === "SIGNAL_RECEIVED") {
          return [...context.signals, event.signal];
        }
        return context.signals;
      },
      currentSignal: ({ event }) => {
        if (event.type === "SIGNAL_RECEIVED") {
          return event.signal;
        }
        return undefined;
      },
    }),
    assignThreat: assign({
      detectedThreat: ({ event }) => {
        if (event.type === "THREAT_DETECTED") {
          return event.threat;
        }
        return undefined;
      },
    }),
    assignActions: assign({
      actionPlan: ({ event }) => {
        if (event.type === "ACTIONS_CREATED") {
          return event.actions;
        }
        return [];
      },
    }),
    assignResults: assign({
      executionResults: ({ event }) => {
        if (event.type === "EXECUTION_COMPLETED") {
          return event.results;
        }
        return [];
      },
    }),
    assignError: assign({
      error: ({ event }) => {
        if (event.type === "ERROR") {
          return event.error;
        }
        return undefined;
      },
    }),
    clearCurrentSignal: assign({
      currentSignal: () => undefined,
    }),
  },
  guards: {
    hasSignals: ({ context }) => context.signals.length > 0,

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
    },
  },
  actors: {
    evaluateSignals: actors.evaluateSignals,
    processThreats: actors.processThreats,
    composeActions: actors.composeActions,
    executeActions: actors.executeActions,
  },
}).createMachine({
  id: "horus",
  initial: "idle",
  context: initialContext,
  states: {
    idle: {
      on: {
        SIGNAL_RECEIVED: {
          target: "evaluating",
          actions: { type: "assignSignal" },
        },
      },
    },
    evaluating: {
      invoke: {
        src: "evaluateSignals",
        input: ({ context }) => ({ context }),
        onDone: [
          {
            target: "processing",
            guard: { type: "isThreat" },
            actions: assign({
              detectedThreat: ({ event }) => {
                console.log("Assigning detected threat:", event.output.threat);
                return event.output.threat;
              },
            }),
          },
          {
            target: "failed",
            guard: { type: "hasError" },
            actions: assign({
              error: ({ event }) => {
                console.error(
                  "Signal evaluation failed with error:",
                  event.output.error
                );
                return event.output.error;
              },
            }),
          },
          {
            target: "idle",
            guard: { type: "isNotThreat" },
            actions: { type: "clearCurrentSignal" },
          },
        ],
        onError: {
          target: "failed",
          actions: [
            assign({
              error: ({ event }) => event.error as Error,
            }),
            ({ context }) =>
              console.error("Error in evaluating state:", context.error),
          ],
        },
      },
      on: {
        // Handle manual transitions for testing
        NO_THREAT_DETECTED: {
          target: "idle",
          actions: { type: "clearCurrentSignal" },
        },
      },
    },
    processing: {
      invoke: {
        src: "processThreats",
        input: ({ context }) => ({ context }),
        onDone: {
          target: "composing",
          actions: assign({
            detectedThreat: ({ event }) => event.output,
          }),
        },
        onError: {
          target: "failed",
          actions: assign({
            error: ({ event }) => event.error as Error,
          }),
        },
      },
    },
    composing: {
      invoke: {
        src: "composeActions",
        input: ({ context }) => ({ context }),
        onDone: {
          target: "executing",
          actions: assign({
            actionPlan: ({ event }) => event.output,
          }),
        },
        onError: {
          target: "failed",
          actions: assign({
            error: ({ event }) => event.error as Error,
          }),
        },
      },
    },
    executing: {
      invoke: {
        src: "executeActions",
        input: ({ context }) => ({ context }),
        onDone: {
          target: "completed",
          actions: assign({
            // @ts-expect-error - Actor output matches executionResults type
            executionResults: ({ event }) => event.output,
          }),
        },
        onError: {
          target: "failed",
          actions: assign({
            error: ({ event }) => event.error as Error,
          }),
        },
      },
    },
    completed: {
      after: {
        1000: "idle",
      },
    },
    failed: {
      on: {
        EVALUATE_SIGNALS: "evaluating",
      },
    },
  },
});
