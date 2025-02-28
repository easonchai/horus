import { setup, assign } from 'xstate';
import { HorusContext, HorusEvent } from './types';

const initialContext: HorusContext = {
  signals: [],
  actionPlan: [],
  executionResults: []
};

export const horusMachine = setup({
  types: {
    context: {} as HorusContext,
    events: {} as HorusEvent,
  },
  actions: {
    assignSignal: assign({
      signals: ({ context, event }) =>
        event.type === 'SIGNAL_RECEIVED'
          ? [...context.signals, event.signal]
          : context.signals,
      currentSignal: ({ event }) =>
        event.type === 'SIGNAL_RECEIVED' ? event.signal : undefined,
    }),
    assignThreat: assign({
      detectedThreat: ({ event }) =>
        event.type === 'THREAT_DETECTED' ? event.threat : undefined,
    }),
    assignActions: assign({
      actionPlan: ({ event }) =>
        event.type === 'ACTIONS_CREATED' ? event.actions : [],
    }),
    assignResults: assign({
      executionResults: ({ event }) =>
        event.type === 'EXECUTION_COMPLETED' ? event.results : [],
    }),
    assignError: assign({
      error: ({ event }) =>
        event.type === 'ERROR' ? event.error : undefined,
    }),
    clearCurrentSignal: assign({
      currentSignal: undefined,
    }),
  },
  guards: {
    hasSignals: ({ context }) => context.signals.length > 0,
  },
}).createMachine({
  id: 'horus',
  initial: 'idle',
  context: initialContext,
  states: {
    idle: {
      on: {
        SIGNAL_RECEIVED: {
          target: 'evaluating',
          actions: 'assignSignal',
        },
      },
    },
    evaluating: {
      invoke: {
        src: 'evaluateSignals',
        onDone: [
          {
            target: 'processing',
            guard: ({ event }) => event.output.isThreat,
            actions: assign({
              detectedThreat: ({ event }) => event.output.threat,
            }),
          },
          {
            target: 'idle',
            guard: ({ event }) => !event.output.isThreat,
            actions: 'clearCurrentSignal',
          },
        ],
        onError: {
          target: 'failed',
          actions: 'assignError',
        },
      },
    },
    processing: {
      invoke: {
        src: 'processThreats',
        onDone: {
          target: 'composing',
          actions: assign({
            detectedThreat: ({ event }) => event.output,
          }),
        },
        onError: {
          target: 'failed',
          actions: 'assignError',
        },
      },
    },
    composing: {
      invoke: {
        src: 'composeActions',
        onDone: {
          target: 'executing',
          actions: assign({
            actionPlan: ({ event }) => event.output,
          }),
        },
        onError: {
          target: 'failed',
          actions: 'assignError',
        },
      },
    },
    executing: {
      invoke: {
        src: 'executeActions',
        onDone: {
          target: 'completed',
          actions: assign({
            executionResults: ({ event }) => event.output,
          }),
        },
        onError: {
          target: 'failed',
          actions: 'assignError',
        },
      },
    },
    completed: {
      after: {
        1000: 'idle',
      },
    },
    failed: {
      on: {
        EVALUATE_SIGNALS: 'evaluating',
      },
    },
  },
});
