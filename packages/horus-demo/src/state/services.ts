import { fromPromise } from 'xstate';
import { SignalEvaluator } from '../services/signal-evaluator';
import { ActionComposer } from '../services/action-composer';
import { ActionExecutor } from '../services/action-executor';
import { AgentService } from '../services/agent-service';

// Load dependency graph
import dependencyGraph from '../data/dependency_graph.json';

// Service instances
const signalEvaluator = new SignalEvaluator();
const actionComposer = new ActionComposer(dependencyGraph);
const actionExecutor = new ActionExecutor();
const agentService = new AgentService();

export const services = {
  evaluateSignals: fromPromise(async ({ context }) => {
    if (!context.currentSignal) {
      throw new Error('No current signal to evaluate');
    }

    return signalEvaluator.evaluateSignal(context.currentSignal);
  }),

  processThreats: fromPromise(async ({ context }) => {
    if (!context.detectedThreat) {
      throw new Error('No threat detected to process');
    }

    return agentService.analyzeThreats(context.detectedThreat, dependencyGraph);
  }),

  composeActions: fromPromise(async ({ context }) => {
    if (!context.detectedThreat) {
      throw new Error('No threat to compose actions for');
    }

    return actionComposer.composeActions(context.detectedThreat);
  }),

  executeActions: fromPromise(async ({ context }) => {
    if (context.actionPlan.length === 0) {
      throw new Error('No actions to execute');
    }

    return actionExecutor.executeActions(context.actionPlan);
  })
};
