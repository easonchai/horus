import { describe, expect, it } from "vitest";
import { evaluateTweetsActionProvider } from "../src/providers/tweet-evaluation.provider";

describe("Tweet Evaluation Provider Tests", () => {
  it("should create the provider instance", () => {
    const provider = evaluateTweetsActionProvider();
    expect(provider).toBeDefined();
  });

  it("should support all networks", () => {
    const provider = evaluateTweetsActionProvider();
    expect(provider.supportsNetwork()).toBe(true);
  });
});
