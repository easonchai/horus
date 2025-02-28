import { DependencyGraph } from "../models/config";
import { Action, Threat } from "../models/types";
import { AgentService } from "./agent-service";
import { ProtocolService } from "./protocol-service";

export class ActionComposer {
  private agentService: AgentService;

  constructor(private dependencyGraph: DependencyGraph) {
    this.agentService = new AgentService();
  }

  public async composeActions(threat: Threat): Promise<Action[]> {
    try {
      // Normalize protocol names to ensure they match the dependency graph
      const normalizedThreat = {
        ...threat,
        affectedProtocols: threat.affectedProtocols.map(
          (protocol) =>
            ProtocolService.getNormalizedProtocolName(protocol) || protocol
        ),
      };

      // Try to use AgentKit for smarter action composition with normalized threat
      const actions = await this.agentService.generateActionPlan(
        normalizedThreat,
        this.dependencyGraph
      );
      return actions;
    } catch (error) {
      console.error("Error composing actions with AgentKit:", error);

      // Fallback to simpler logic
      const actions: Action[] = [];

      // For each affected protocol (normalize names first)
      const normalizedProtocols = threat.affectedProtocols.map(
        (protocol) =>
          ProtocolService.getNormalizedProtocolName(protocol) || protocol
      );

      for (const protocol of normalizedProtocols) {
        // Get tokens dependent on this protocol
        const dependentTokens = this.dependencyGraph[protocol] || [];

        // For each token, create an appropriate action
        for (const token of dependentTokens) {
          // If token is affected, withdraw it
          if (threat.affectedTokens.includes(token)) {
            actions.push({
              type: "withdraw",
              protocol,
              token,
              params: { amount: "100%" },
            });
          }
          // Otherwise, consider swapping to a safer token
          else {
            actions.push({
              type: "swap",
              protocol,
              token,
              params: { toToken: "USDC", amount: "100%" },
            });
          }
        }
      }

      return actions;
    }
  }
}
