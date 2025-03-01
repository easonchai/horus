/**
 * Example showing how to use the signal evaluator with a dependency graph
 * to detect security threats from tweets
 */

import { Signal } from "../models/types";
import { DependencyGraphService } from "../services/dependency-graph-service";
import { SignalEvaluator } from "../services/signal-evaluator";

// Sample tweets for testing
const testTweets = [
  {
    content:
      "Just heard about a major exploit in Uniswap. Users with USDC-USDT LP positions should withdraw immediately! #DeFi #security",
    expectThreat: true,
  },
  {
    content:
      "The Beefy Finance vaults on Base are performing incredibly well this week! Great yields on the USDC-USDT pools.",
    expectThreat: false,
  },
  {
    content:
      "CRITICAL: UniswapV3 contract vulnerability discovered on Base chain (chainId: 84532). All USDC pairs potentially at risk. Withdraw now!",
    expectThreat: true,
  },
];

/**
 * Run a simulation of the threat detection system
 */
async function runThreatDetection() {
  const evaluator = new SignalEvaluator();

  console.log("🛡️ HORUS DEFI PROTECTION SYSTEM - THREAT DETECTION TEST");
  console.log("==================================================");
  console.log();

  // Get the dependency graph from the service
  const dependencyGraph = DependencyGraphService.getDependencyGraph();

  // Display available protocols from the dependency graph
  console.log("📊 DEPENDENCY GRAPH OVERVIEW:");
  console.log(
    `Available Protocols: ${Object.keys(dependencyGraph).join(", ")}`
  );

  // Example of accessing specific protocol dependencies
  if (Object.keys(dependencyGraph).length > 0) {
    const sampleProtocol = Object.keys(dependencyGraph)[0];
    console.log(
      `${sampleProtocol} Dependencies: ${dependencyGraph[sampleProtocol].join(
        ", "
      )}`
    );
  }

  // Display sample tokens by chain
  const baseChainTokens = DependencyGraphService.getTokensByChain("84532");
  console.log(`Base Chain Tokens: ${baseChainTokens.join(", ")}`);
  console.log("==================================================");
  console.log();

  for (const [index, tweet] of testTweets.entries()) {
    console.log(`📝 ANALYZING TWEET ${index + 1}:`);
    console.log(`"${tweet.content}"`);
    console.log();

    const signal: Signal = {
      source: "twitter",
      content: tweet.content,
      timestamp: Date.now(),
    };

    try {
      // In a real scenario, this would send the prompt to an LLM and parse the response
      // For this example, we're using the keyword-based fallback
      const result = await evaluator.evaluateSignal(signal);

      console.log(`🔍 ANALYSIS RESULT:`);
      console.log(`Is Threat: ${result.isThreat ? "✅ YES" : "❌ NO"}`);

      if (result.isThreat && result.threat) {
        console.log(`Severity: ${result.threat.severity}`);
        console.log(`Description: ${result.threat.description}`);
        console.log(
          `Affected Protocols: ${result.threat.affectedProtocols.join(", ")}`
        );
        console.log(
          `Affected Tokens: ${result.threat.affectedTokens.join(", ")}`
        );
        console.log(`Chain: ${result.threat.chain}`);
      }

      console.log("==================================================");
    } catch (error) {
      console.error(`Error analyzing tweet: ${error}`);
    }
  }
}

// Run the example if this file is executed directly
if (require.main === module) {
  runThreatDetection()
    .then(() => console.log("Threat detection test completed"))
    .catch((error) => console.error("Error in threat detection test:", error));
}
