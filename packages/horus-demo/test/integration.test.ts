import { describe, it, expect, vi } from 'vitest';
import { createActor } from 'xstate';
import { horusMachine } from '../src/state/machine';
import { services } from '../src/state/services';
import { SignalEvaluator } from '../src/services/signal-evaluator';
import { ActionComposer } from '../src/services/action-composer';
import { ActionExecutor } from '../src/services/action-executor';

// Mock the services for testing
vi.mock('../src/services/signal-evaluator');
vi.mock('../src/services/action-composer');
vi.mock('../src/services/action-executor');

describe('Horus Integration', () => {
  it('should process a security threat through all states', async () => {
    // Setup mocks
    vi.mocked(SignalEvaluator.prototype.evaluateSignal).mockResolvedValue({
      isThreat: true,
      threat: {
        description: 'Test threat',
        affectedProtocols: ['uniswap'],
        affectedTokens: ['USDC'],
        chain: 'ethereum',
        severity: 'high'
      }
    });

    vi.mocked(ActionComposer.prototype.composeActions).mockResolvedValue([
      {
        type: 'withdraw',
        protocol: 'uniswap',
        token: 'USDC',
        params: { amount: '100%' }
      }
    ]);

    vi.mocked(ActionExecutor.prototype.executeActions).mockResolvedValue([
      {
        action: {
          type: 'withdraw',
          protocol: 'uniswap',
          token: 'USDC',
          params: { amount: '100%' }
        },
        status: 'success',
        txHash: '0xtest',
        timestamp: Date.now()
      }
    ]);

    // Create actor with mocked services
    const actor = createActor(horusMachine, { services }).start();

    // Send a signal
    actor.send({
      type: 'SIGNAL_RECEIVED',
      signal: {
        source: 'twitter',
        content: 'Test security threat',
        timestamp: Date.now()
      }
    });

    // Wait for processing to complete
    await new Promise<void>(resolve => {
      const subscription = actor.subscribe(state => {
        if (state.value === 'completed') {
          subscription.unsubscribe();
          resolve();
        }
      });
    });

    // Verify final state
    const snapshot = actor.getSnapshot();
    expect(snapshot.value).toBe('completed');
    expect(snapshot.context.actionPlan.length).toBe(1);
    expect(snapshot.context.executionResults.length).toBe(1);

    // Verify it returns to idle after delay
    vi.advanceTimersByTime(1500);
    expect(actor.getSnapshot().value).toBe('idle');
  });
});
