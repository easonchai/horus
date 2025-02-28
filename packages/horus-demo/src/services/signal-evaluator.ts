import { Signal, Threat } from '../models/types';
import { AgentService } from './agent-service';

export class SignalEvaluator {
  private agentService: AgentService;
  // For basic keyword-based evaluation
  private threatKeywords = [
    'vulnerability', 'exploit', 'attack', 'hacked',
    'security', 'breach', 'risk', 'urgent', 'compromise'
  ];

  constructor() {
    this.agentService = new AgentService();
  }

  public async evaluateSignal(signal: Signal): Promise<{ isThreat: boolean; threat?: Threat }> {
    try {
      // Use AgentKit for evaluation
      const evaluation = await this.agentService.evaluateSignal(signal.content);
      return evaluation;
    } catch (error) {
      console.error('Error evaluating signal with AgentKit:', error);

      // Fall back to simple keyword matching
      const content = signal.content.toLowerCase();
      const containsThreatKeywords = this.threatKeywords.some(
        keyword => content.includes(keyword.toLowerCase())
      );

      // Simple protocol detection
      const protocols = ['uniswap', 'aave', 'curve', 'compound', 'balancer']
        .filter(protocol => content.toLowerCase().includes(protocol.toLowerCase()));

      // Simple token detection
      const tokens = ['eth', 'usdc', 'usdt', 'dai', 'wbtc']
        .filter(token => content.toLowerCase().includes(token.toLowerCase()));

      if (containsThreatKeywords && protocols.length > 0) {
        return {
          isThreat: true,
          threat: {
            description: `Potential threat detected in signal: ${signal.content}`,
            affectedProtocols: protocols,
            affectedTokens: tokens.length > 0 ? tokens : ['unknown'],
            chain: 'ethereum', // Default for now
            severity: 'medium' // Default for now
          }
        };
      }

      return { isThreat: false };
    }
  }
}
