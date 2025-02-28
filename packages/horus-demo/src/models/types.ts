// Signal types
export type SignalSource = "twitter" | "discord" | "other";

export interface Signal {
  source: SignalSource;
  content: string;
  timestamp: number;
}

// Threat types
export type SeverityLevel = "low" | "medium" | "high" | "critical";

export interface Threat {
  description: string;
  affectedProtocols: string[];
  affectedTokens: string[];
  chain: string;
  severity: SeverityLevel;
}

// Signal evaluation results
export interface SignalEvaluationResult {
  isThreat: boolean;
  threat?: Threat;
  error?: Error;
}

// Action types
export type ActionType = "swap" | "withdraw" | "revoke";

export interface Action {
  type: ActionType;
  protocol: string;
  token: string;
  params: Record<string, string | number | boolean>;
}

// Token types
export interface Token {
  name: string;
  symbol: string;
  decimals: number;
  networks: Record<string, string>; // chainId -> address mapping
}
