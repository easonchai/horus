import { Action, SignalEvaluationResult, Threat } from "../models/types";
import { DependencyGraphService } from "./dependency-graph-service";
import { ProtocolService } from "./protocol-service";
import { TokenService } from "./token-service";

// This is a placeholder for the real AgentKit implementation
export class AgentService {
  public async evaluateSignal(
    content: string
  ): Promise<SignalEvaluationResult> {
    // Simulate AI response (we will use an AI here in the future)
    const isThreat =
      content.toLowerCase().includes("vulnerability") ||
      content.toLowerCase().includes("exploit") ||
      content.toLowerCase().includes("risk") ||
      content.toLowerCase().includes("alert");

    // Create basic threat representation
    return {
      isThreat,
      threat: isThreat
        ? {
            description: `AI evaluated threat: ${content}`,
            affectedProtocols: this.extractProtocols(content),
            affectedTokens: this.extractTokens(content),
            chain: this.extractChain(content) || "ethereum",
            severity: this.determineSeverity(content),
          }
        : undefined,
    };
  }

  public async analyzeThreats(threat: Threat): Promise<Threat> {
    // Enhance threat with more analysis
    return {
      ...threat,
      severity: threat.severity === "medium" ? "high" : threat.severity,
      affectedTokens: [
        ...threat.affectedTokens,
        ...this.getDependentTokens(threat.affectedProtocols),
      ],
    };
  }

  public async generateActionPlan(threat: Threat): Promise<Action[]> {
    // Get the dependency graph from the service
    const dependencies = DependencyGraphService.getDependencyGraph();

    // Generate actions based on threat
    const actions: Action[] = [];

    // For protocols directly mentioned in the threat
    for (const protocol of threat.affectedProtocols) {
      if (dependencies[protocol]) {
        for (const token of dependencies[protocol]) {
          // If threat is critical, withdraw everything
          if (threat.severity === "critical") {
            actions.push({
              type: "withdraw",
              protocol,
              token,
              params: { amount: "100%" },
            });
          }
          // For high severity, swap affected tokens
          else if (
            threat.severity === "high" &&
            threat.affectedTokens.includes(token)
          ) {
            actions.push({
              type: "swap",
              protocol,
              token,
              params: { toToken: "ETH", amount: "100%" },
            });
          }
          // For medium severity, consider revoking approvals
          else if (threat.severity === "medium") {
            actions.push({
              type: "revoke",
              protocol,
              token,
              params: {},
            });
          }
        }
      }
    }

    return actions;
  }

  // Helper methods
  private extractProtocols(content: string): string[] {
    // Get all protocol names from the configuration
    const protocolNames = ProtocolService.getAllProtocolNames().map((name) =>
      name.toLowerCase()
    );

    // Find matches in the content
    const matches = protocolNames.filter((name) =>
      content.toLowerCase().includes(name)
    );

    // Map back to exact protocol names from configuration
    return matches.map(
      (match) => ProtocolService.getNormalizedProtocolName(match) || match
    );
  }

  private extractTokens(content: string): string[] {
    return TokenService.detectTokensInContent(content);
  }

  private extractChain(content: string): string | null {
    const chains = [
      { name: "ethereum", keywords: ["ethereum", "eth"] },
      { name: "polygon", keywords: ["polygon", "matic"] },
      { name: "optimism", keywords: ["optimism", "op"] },
      { name: "arbitrum", keywords: ["arbitrum", "arb"] },
    ];

    for (const chain of chains) {
      if (chain.keywords.some((k) => content.toLowerCase().includes(k))) {
        return chain.name;
      }
    }

    return null;
  }

  private determineSeverity(
    content: string
  ): "low" | "medium" | "high" | "critical" {
    const contentLower = content.toLowerCase();
    if (contentLower.includes("critical") || contentLower.includes("urgent")) {
      return "critical";
    } else if (
      contentLower.includes("high") ||
      contentLower.includes("severe")
    ) {
      return "high";
    } else if (
      contentLower.includes("medium") ||
      contentLower.includes("moderate")
    ) {
      return "medium";
    } else {
      return "low";
    }
  }

  private getDependentTokens(protocols: string[]): string[] {
    const tokens: string[] = [];
    for (const protocol of protocols) {
      tokens.push(
        ...DependencyGraphService.getDependenciesByProtocol(protocol)
      );
    }
    return [...new Set(tokens)]; // Remove duplicates
  }
}
