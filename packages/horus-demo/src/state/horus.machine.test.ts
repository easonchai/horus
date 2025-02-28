import { createActor } from 'xstate';
import { horusMachine } from './horus.machine';
import { describe, it, expect } from 'vitest';

describe('Horus State Machine', () => {
  it('should transition to evaluating on SIGNAL_RECEIVED', () => {
    const actor = createActor(horusMachine).start();

    actor.send({
      type: 'SIGNAL_RECEIVED',
      signal: {
        id: '1',
        source: 'twitter',
        content: 'Test signal',
        timestamp: Date.now()
      }
    });

    expect(actor.getSnapshot().value).toBe('evaluating');
    expect(actor.getSnapshot().context.signals.length).toBe(1);
  });
});
