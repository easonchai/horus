import { Threat, Action } from '../models/types';
import { DependencyGraph } from '../models/config';
import { AgentService } from './agent-service';

export class ActionComposer {
  private agentService: AgentService;

  constructor(private dependencyGraph: DependencyGraph) {
    this.agentService = new AgentService();
  }

  public async composeActions(threat: Threat): Promise<Action[]> {
    try {
      // Try to use AgentKit for smarter action composition
      const actions = await this.agentService.generateActionPlan(threat, this.dependencyGraph);
      return actions;
    } catch (error) {
      console.error('Error composing actions with AgentKit:', error);

      // Fallback to simpler logic
      const actions: Action[] = [];

      // For each affected protocol
      for (const protocol of threat.affectedProtocols) {
        // Get tokens dependent on this protocol
        const dependentTokens = this.dependencyGraph[protocol] || [];

        // For each token, create an appropriate action
        for (const token of dependentTokens) {
          // If token is affected, withdraw it
          if (threat.affectedTokens.includes(token)) {
            actions.push({
              type: 'withdraw',
              protocol,
              token,
              params: { amount: '100%' }
            });
          }
          // Otherwise, consider swapping to a safer token
          else {
            actions.push({
              type: 'swap',
              protocol,
              token,
              params: { toToken: 'USDC', amount: '100%' }
            });
          }
        }
      }

      return actions;
    }
  }
}
