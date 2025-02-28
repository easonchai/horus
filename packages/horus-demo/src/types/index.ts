export type Signal = {
  source: "twitter" | "hacken";
  content: string;
  timestamp: number;
};

export type Threat = {
  description: string;
  affectedProtocols: string[];
  affectedTokens: string[];
  chain: string;
  severity: "low" | "medium" | "high" | "critical";
};

export type Action = {
  type: "swap" | "withdraw" | "revoke";
  protocol: string;
  token: string;
  params: Record<string, string | number | boolean>;
};
