import { DependencyGraph } from "../models/config";
import { Signal, SignalEvaluationResult } from "../models/types";
import { AgentService } from "./agent-service";
import { DependencyGraphService } from "./dependency-graph-service";

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
    // Assuming AgentService now requires configuration, we'll pass an empty object
    // For the linter error, will need to update AgentService or mock it properly
    this.agentService = new AgentService({} as any); // Using 'as any' temporarily to bypass the linter error
  }

  public async evaluateSignal(
    signal: Signal,
    dependencyGraph?: DependencyGraph
  ): Promise<SignalEvaluationResult> {
    try {
      // Use the DependencyGraphService if no dependency graph is provided
      const graphData =
        dependencyGraph || DependencyGraphService.getDependencyGraph();

      // In a real implementation, you would call your LLM service with the prompt
      const prompt = this.buildLLMPrompt(signal.content, graphData);
      console.log("Generated LLM prompt:", prompt);

      // Here's how you might use the LLM service:
      // const llmResponse = await callLLMService(prompt);
      // return parseLLMResponse(llmResponse);

      // For now, returning a basic result based on keywords
      return {
        isThreat: this.threatKeywords.some((keyword) =>
          signal.content.toLowerCase().includes(keyword.toLowerCase())
        ),
        threat: undefined,
      };
    } catch (error) {
      console.error("Error evaluating signal:", error);
      return {
        isThreat: false,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }

  /**
   * Builds a prompt for an LLM to evaluate a tweet for security threats
   * and determine if they affect tokens or protocols in the dependency graph
   */
  public buildLLMPrompt(
    tweetContent: string,
    dependencyGraph?: DependencyGraph
  ): string {
    // Get the dependency graph data if not provided
    const graphData =
      dependencyGraph || DependencyGraphService.getDependencyGraph();

    return `
# Security Threat Analysis

## Context
You are a specialized security analyst for decentralized finance (DeFi) protocols. Your task is to:
1. Analyze the provided tweet for potential security threats
2. Determine if these threats affect any protocols or tokens in our dependency graph
3. Provide a structured evaluation of the threat

## Tweet Content
"""
${tweetContent}
"""

## Dependency Graph
${JSON.stringify(graphData, null, 2)}

## Evaluation Instructions

1. **Threat Detection**:
   - Carefully analyze the tweet for indications of security issues in DeFi protocols
   - Consider exploits, vulnerabilities, attacks, hacks, breaches, or other security risks
   - Differentiate between general market information and actual security threats
   - Determine if this is referring to a past event or a current/ongoing threat

2. **Impact Analysis**:
   - If a threat is detected, identify which specific protocols, chains, or tokens are affected
   - Cross-reference with our dependency graph to determine if any of our integrated protocols or tokens are impacted
   - Consider direct impacts (explicitly mentioned) and indirect impacts (dependencies that rely on affected components)

3. **Required Response Format**:
   Provide your analysis in the following JSON structure:
   \`\`\`json
   {
     "isThreat": boolean,
     "threat": {
       "description": "Clear explanation of the threat",
       "affectedProtocols": ["List of affected protocol names in our dependency graph"],
       "affectedTokens": ["List of affected token symbols in our dependency graph"],
       "chain": "Affected blockchain (chainId)",
       "severity": "low|medium|high|critical"
     }
   }
   \`\`\`

   If no threat is detected, return:
   \`\`\`json
   {
     "isThreat": false
   }
   \`\`\`

## Severity Guidelines:
- **Low**: Minor vulnerabilities with limited impact, no funds at immediate risk
- **Medium**: Exploitable vulnerabilities that could affect some users or limited funds
- **High**: Active exploits or vulnerabilities that put significant funds at risk
- **Critical**: Ongoing attacks with confirmed loss of funds or catastrophic protocol failure

## Important
- Base your analysis solely on the content of the tweet and our dependency graph
- Do not speculate beyond the available information
- Be conservative in threat classification - only mark as a threat if there's clear evidence
- For affected components, only include those explicitly present in our dependency graph
- Pay special attention to protocols like Uniswap, Beefy, etc. that appear in our dependency graph
- Consider indirect effects: if a token in a liquidity pair is compromised, the pair and any derivative products are also affected`;
  }
}
