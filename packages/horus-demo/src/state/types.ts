import { Signal, Threat, Action } from '../models/types';

export interface HorusContext {
  signals: Signal[];
  currentSignal?: Signal;
  detectedThreat?: Threat;
  actionPlan: Action[];
  executionResults: { success: boolean; txHash: string; action: Action }[];
  error?: Error;
}

export type HorusEvent =
  | { type: 'SIGNAL_RECEIVED'; signal: Signal }
  | { type: 'EVALUATE_SIGNALS' }
  | { type: 'THREAT_DETECTED'; threat: Threat }
  | { type: 'NO_THREAT_DETECTED' }
  | { type: 'ACTIONS_CREATED'; actions: Action[] }
  | { type: 'EXECUTION_COMPLETED'; results: { success: boolean; txHash: string; action: Action }[] }
  | { type: 'ERROR'; error: Error };
