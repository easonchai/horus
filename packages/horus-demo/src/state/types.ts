import { Action, Signal, Threat } from "../models/types";
import { ActionExecutionResult } from "../services/action-executor";

export interface HorusContext {
  signals: Signal[];
  currentSignal?: Signal;
  detectedThreat?: Threat;
  actionPlan: Action[];
  executionResults: ActionExecutionResult[];
  error?: Error;
  dependencyGraph?: {
    tokens: string[];
    protocols: string[];
  };
  analysisText?: string;
}

export type HorusEvent =
  | { type: "SIGNAL_RECEIVED"; signal: Signal }
  | { type: "EVALUATE_SIGNALS" }
  | { type: "THREAT_DETECTED"; threat: Threat }
  | { type: "NO_THREAT_DETECTED" }
  | { type: "ACTIONS_CREATED"; actions: Action[] }
  | { type: "EXECUTION_COMPLETED"; results: ActionExecutionResult[] }
  | { type: "ERROR"; error: Error };
