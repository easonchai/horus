import { DependencyGraph } from "../models/config";
import { Action, Threat } from "../models/types";
import { AgentService } from "./agent-service";
import { ProtocolService } from "./protocol-service";
import { TokenService } from "./token-service";

export class ActionComposer {
  private agentService: AgentService;
  private readonly DEFAULT_SAFE_TOKEN = "USDC";
  private validatedSafeToken: string;

  constructor(private dependencyGraph: DependencyGraph) {
    this.agentService = new AgentService();

    // Validate DEFAULT_SAFE_TOKEN at initialization time
    if (!TokenService.isValidToken(this.DEFAULT_SAFE_TOKEN)) {
      console.warn(
        `Default safe token "${this.DEFAULT_SAFE_TOKEN}" not found in configuration. Will use first available token as fallback.`
      );
      // Set to first available token or keep default as last resort
      this.validatedSafeToken =
        TokenService.getAllTokenSymbols()[0] || this.DEFAULT_SAFE_TOKEN;
    } else {
      // Use the normalized symbol to ensure consistent casing
      this.validatedSafeToken =
        TokenService.getNormalizedTokenSymbol(this.DEFAULT_SAFE_TOKEN) ||
        this.DEFAULT_SAFE_TOKEN;
    }
    console.log(
      `Using "${this.validatedSafeToken}" as the safe token for swaps`
    );
  }

  public async composeActions(threat: Threat): Promise<Action[]> {
    try {
      // Normalize protocol names and token symbols to ensure they match the dependency graph
      const normalizedThreat = {
        ...threat,
        affectedProtocols: threat.affectedProtocols.map(
          (protocol) =>
            ProtocolService.getNormalizedProtocolName(protocol) || protocol
        ),
        affectedTokens: threat.affectedTokens.map(
          (token) => TokenService.getNormalizedTokenSymbol(token) || token
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

      // Get normalized token symbols
      const normalizedAffectedTokens = threat.affectedTokens.map(
        (token) => TokenService.getNormalizedTokenSymbol(token) || token
      );

      // Use the validated safe token (established in constructor)
      const safeToken = this.validatedSafeToken;

      for (const protocol of normalizedProtocols) {
        // Get tokens dependent on this protocol
        const dependentTokens = this.dependencyGraph[protocol] || [];

        // For each token, create an appropriate action
        for (const token of dependentTokens) {
          // Normalize the token symbol
          const normalizedToken =
            TokenService.getNormalizedTokenSymbol(token) || token;

          // If token is affected, withdraw it
          if (normalizedAffectedTokens.includes(normalizedToken)) {
            actions.push({
              type: "withdraw",
              protocol,
              token: normalizedToken,
              params: { amount: "100%" },
            });
          }
          // Otherwise, consider swapping to a safer token
          else {
            actions.push({
              type: "swap",
              protocol,
              token: normalizedToken,
              params: { toToken: safeToken, amount: "100%" },
            });
          }
        }
      }

      return actions;
    }
  }
}
