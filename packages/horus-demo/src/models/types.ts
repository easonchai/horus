export type SignalSource = 'twitter' | 'discord' | 'other';

export interface Signal {
  id: string;
  source: SignalSource;
  content: string;
  timestamp: number;
}

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface Threat {
  description: string;
  affectedProtocols: string[];
  affectedTokens: string[];
  chain: string;
  severity: SeverityLevel;
}

export type ActionType = 'swap' | 'withdraw' | 'revoke';

export interface Action {
  type: ActionType;
  protocol: string;
  token: string;
  params: Record<string, unknown>;
}
