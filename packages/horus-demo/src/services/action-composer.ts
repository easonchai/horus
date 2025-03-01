import { ViemWalletProvider, WalletProvider } from "@coinbase/agentkit";
import { DependencyGraph } from "../models/config";
import { Action, Threat } from "../models/types";
import { AgentService } from "./agent-service";
import { DependencyGraphService } from "./dependency-graph-service";
import { ProtocolService } from "./protocol-service";
import { TokenService } from "./token-service";
import { WalletService } from "./wallet-service";

export class ActionComposer {
  private agentService: AgentService;
  private readonly DEFAULT_SAFE_TOKEN = "USDC";
  private validatedSafeToken: string;
  private dependencyGraph: DependencyGraph;

  constructor() {
    // Initialize AgentService with required configuration
    const walletService = new WalletService();
    const walletClient = walletService.getWalletClient();
    const walletProvider = walletClient
      ? new ViemWalletProvider(walletClient)
      : undefined;

    this.agentService = new AgentService({
      walletProvider: walletProvider as WalletProvider,
      actionProviders: [],
      systemMessage:
        "You are a security action composer for DeFi protocols. You recommend actions to protect assets from threats.",
    });

    this.dependencyGraph = DependencyGraphService.getDependencyGraph();

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

      // Create array to hold actions
      const actions: Action[] = [];

      // Generate prompt for action composition - can be used with this.agentService if implemented in future
      /* const prompt = `
        Generate actions to respond to this security threat:
        ${JSON.stringify(normalizedThreat, null, 2)}
        
        Our project depends on: ${JSON.stringify(this.dependencyGraph, null, 2)}
        
        Provide actions using type: "swap", "withdraw", or "revoke"
      `; */

      try {
        // Use manual action composition based on threat severity
        if (
          normalizedThreat.severity === "critical" ||
          normalizedThreat.severity === "high"
        ) {
          // Add a default action for any affected tokens, or a default one if none
          if (normalizedThreat.affectedTokens.length > 0) {
            const token = normalizedThreat.affectedTokens[0];
            actions.push({
              type: "withdraw",
              protocol: "UniswapV3", // Use a protocol we know exists in our config
              token,
              params: { amount: "100%" },
            });
          } else {
            // Fallback action with USDC if no affected tokens
            actions.push({
              type: "swap",
              protocol: "UniswapV3",
              token: "USDC",
              params: { toToken: "ETH", amount: "100%" },
            });
          }
        }
      } catch (innerError) {
        console.error(
          "[ActionComposer] Error in manual action composition:",
          innerError
        );
      }

      return actions;
    } catch (error) {
      console.error("[ActionComposer] Error composing actions:", error);
      return [];
    }
  }
}
