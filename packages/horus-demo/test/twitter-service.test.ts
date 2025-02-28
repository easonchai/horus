import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TwitterPoller } from "../src/mock/tweet-generator";
import { Signal } from "../src/models/types";

describe("TwitterPoller", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should call callback with signal when polling", () => {
    const mockCallback = vi.fn();
    const poller = new TwitterPoller(mockCallback);

    poller.start(1000);

    vi.advanceTimersByTime(1000);
    expect(mockCallback).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1000);
    expect(mockCallback).toHaveBeenCalledTimes(2);

    poller.stop();
  });

  it("should convert Tweet to Signal format", () => {
    let capturedSignal: Signal | null = null;
    const callback = (signal: Signal) => {
      capturedSignal = signal;
    };

    const poller = new TwitterPoller(callback);
    poller.start(1000);
    vi.advanceTimersByTime(1000);

    expect(capturedSignal).not.toBeNull();
    expect(capturedSignal?.source).toBe("twitter");
    expect(typeof capturedSignal?.content).toBe("string");
    expect(typeof capturedSignal?.timestamp).toBe("number");

    poller.stop();
  });
});
