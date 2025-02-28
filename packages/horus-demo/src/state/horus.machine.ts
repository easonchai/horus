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
      // We'll add the service later
      on: {
        THREAT_DETECTED: {
          target: 'processing',
          actions: 'assignThreat',
        },
        NO_THREAT_DETECTED: {
          target: 'idle',
          actions: 'clearCurrentSignal',
        },
        ERROR: {
          target: 'failed',
          actions: 'assignError',
        }
      }
    },
    processing: {
      // We'll add the service later
      on: {
        ACTIONS_CREATED: {
          target: 'executing',
          actions: 'assignActions',
        },
        ERROR: {
          target: 'failed',
          actions: 'assignError',
        }
      }
    },
    executing: {
      // We'll add the service later
      on: {
        EXECUTION_COMPLETED: {
          target: 'completed',
          actions: 'assignResults',
        },
        ERROR: {
          target: 'failed',
          actions: 'assignError',
        }
      }
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
