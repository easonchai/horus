import "reflect-metadata";
import { describe, expect, it } from "vitest";
import { actors } from "../src/state/actors";

describe("actors", () => {
  it("should have evaluateSignals actor", () => {
    expect(actors).toBeDefined();
    expect(actors.evaluateSignals).toBeDefined();
  });
});
