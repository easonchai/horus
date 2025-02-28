import { describe, it, expect } from 'vitest';
import { greet } from '../index';

describe('greet function', () => {
  it('should return default greeting when no name is provided', () => {
    expect(greet()).toBe('Hello, world!');
  });

  it('should return personalized greeting when name is provided', () => {
    expect(greet('Horus')).toBe('Hello, Horus!');
  });
});
