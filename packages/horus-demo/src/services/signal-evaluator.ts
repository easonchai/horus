import { Signal, SignalEvaluationResult, Threat } from "../models/types";
import { AgentService } from "./agent-service";
import { ProtocolService } from "./protocol-service";
import { TokenService } from "./token-service";

export class SignalEvaluator {
  private agentService: AgentService;
  // For basic keyword-based evaluation
  private threatKeywords = [
    "vulnerability",
    "exploit",
    "attack",
    "hacked",
    "security",
    "breach",
    "risk",
    "urgent",
    "compromise",
  ];

  constructor() {
    this.agentService = new AgentService();
  }

  public async evaluateSignal(signal: Signal): Promise<SignalEvaluationResult> {
    try {
      // Use AgentKit for evaluation
      const evaluation = await this.agentService.evaluateSignal(signal.content);
      console.log("AgentKit evaluation result:", evaluation);
      return evaluation;
    } catch (error) {
      console.error("Error evaluating signal with AgentKit:", error);

      // Fall back to simple keyword matching with enhanced error handling
      return this.fallbackSignalEvaluation(signal);
    }
  }

  /**
   * Fallback evaluation method when AgentKit is unavailable
   * Uses keyword matching and protocol detection for basic threat evaluation
   */
  private fallbackSignalEvaluation(signal: Signal): SignalEvaluationResult {
    console.log("Using fallback signal evaluation for:", signal.content);
    const content = signal.content.toLowerCase();

    // Check for threat keywords
    const containsThreatKeywords = this.threatKeywords.some((keyword) =>
      content.includes(keyword.toLowerCase())
    );

    // Detect protocols with enhanced error handling
    const protocols = this.detectProtocols(content);
    console.log("Detected protocols:", protocols);

    // Simple token detection
    const tokens = this.detectTokens(content);
    console.log("Detected tokens:", tokens);

    // Create threat if keywords and protocols are found
    if (containsThreatKeywords && protocols.length > 0) {
      const threat: Threat = {
        description: `Potential threat detected in signal: ${signal.content}`,
        affectedProtocols: protocols,
        affectedTokens: tokens.length > 0 ? tokens : ["unknown"],
        chain: "ethereum", // Default for now
        severity: this.determineSeverity(content),
      };

      console.log("Fallback evaluation created threat:", threat);
      return {
        isThreat: true,
        threat,
      };
    }

    // Handle case where there are keywords but no protocols
    if (containsThreatKeywords) {
      console.log("Threat keywords found, but no specific protocols detected");
    }

    // Return no-threat result
    return { isThreat: false };
  }

  /**
   * Detect protocols mentioned in content with enhanced error handling
   */
  private detectProtocols(content: string): string[] {
    try {
      // Get all protocol names from the configuration
      const protocolNames = ProtocolService.getAllProtocolNames();

      if (!protocolNames || protocolNames.length === 0) {
        console.warn("No protocol names available from ProtocolService");
        return [];
      }

      // Convert to lowercase for matching
      const protocolNamesLower = protocolNames.map((name) =>
        name.toLowerCase()
      );

      // Find matches in the content
      const matchedProtocols = protocolNamesLower.filter((name) =>
        content.includes(name)
      );

      if (matchedProtocols.length === 0) {
        return [];
      }

      // Normalize protocol names and handle missing matches gracefully
      return matchedProtocols.map((match) => {
        const normalized = ProtocolService.getNormalizedProtocolName(match);
        if (!normalized) {
          console.warn(`Could not normalize protocol name: ${match}`);
          return match; // Fall back to the matched name
        }
        return normalized;
      });
    } catch (error) {
      console.error("Error in protocol detection:", error);
      return []; // Return empty array on error
    }
  }

  /**
   * Detect tokens mentioned in content
   */
  private detectTokens(content: string): string[] {
    return TokenService.detectTokensInContent(content);
  }

  /**
   * Determine severity based on content keywords
   */
  private determineSeverity(
    content: string
  ): "low" | "medium" | "high" | "critical" {
    if (content.includes("critical") || content.includes("urgent")) {
      return "critical";
    } else if (content.includes("high") || content.includes("severe")) {
      return "high";
    } else if (content.includes("medium") || content.includes("moderate")) {
      return "medium";
    } else {
      return "low";
    }
  }
}
