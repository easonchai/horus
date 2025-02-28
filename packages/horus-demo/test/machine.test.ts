import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { horusMachine } from '../src/state/machine';

describe('Horus State Machine', () => {
  it('should transition to evaluating on SIGNAL_RECEIVED', () => {
    const actor = createActor(horusMachine).start();

    actor.send({
      type: 'SIGNAL_RECEIVED',
      signal: {
        source: 'twitter',
        content: 'Test signal',
        timestamp: Date.now()
      }
    });

    expect(actor.getSnapshot().value).toBe('evaluating');
    expect(actor.getSnapshot().context.signals.length).toBe(1);
  });

  it('should clear current signal when transition back to idle', () => {
    const actor = createActor(horusMachine).start();

    // First send a signal
    actor.send({
      type: 'SIGNAL_RECEIVED',
      signal: {
        source: 'twitter',
        content: 'Test signal',
        timestamp: Date.now()
      }
    });

    // Then manually trigger NO_THREAT_DETECTED (normally done by service)
    actor.send({ type: 'NO_THREAT_DETECTED' });

    expect(actor.getSnapshot().value).toBe('idle');
    expect(actor.getSnapshot().context.currentSignal).toBeUndefined();
  });
});
