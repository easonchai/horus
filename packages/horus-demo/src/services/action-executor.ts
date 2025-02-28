import { Action } from "../models/types";
import { TokenService } from "./token-service";

export interface ActionExecutionResult {
  action: Action;
  status: "success" | "failed";
  txHash?: string;
  tokenAddress?: string;
  error?: string;
  timestamp: number;
}

export class ActionExecutor {
  private readonly DEFAULT_CHAIN_ID = "84532"; // Base Sepolia

  // In a real implementation, this would connect to the blockchain
  public async executeActions(
    actions: Action[]
  ): Promise<ActionExecutionResult[]> {
    const results: ActionExecutionResult[] = [];

    for (const action of actions) {
      try {
        // Validate token exists in configuration
        const normalizedToken = TokenService.getNormalizedTokenSymbol(
          action.token
        );
        if (!normalizedToken) {
          console.warn(`Invalid token ${action.token} - skipping action`);
          results.push({
            action,
            status: "failed",
            error: `Invalid token: ${action.token}`,
            timestamp: Date.now(),
          });
          continue;
        }

        // Get token address from configuration (for a real implementation)
        const tokenAddress = TokenService.getTokenAddress(
          normalizedToken,
          this.DEFAULT_CHAIN_ID
        );
        if (!tokenAddress) {
          console.warn(
            `No address found for token ${normalizedToken} on chain ${this.DEFAULT_CHAIN_ID} - skipping action`
          );
          results.push({
            action,
            status: "failed",
            error: `No token address available for ${normalizedToken}`,
            timestamp: Date.now(),
          });
          continue;
        }

        // Simulate execution delay
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Log the action with token address
        console.log(
          `Executing ${action.type} for ${normalizedToken} (${tokenAddress}) on ${action.protocol}`
        );

        // Add to results
        results.push({
          action: {
            ...action,
            token: normalizedToken, // Use normalized token in result
          },
          status: "success",
          txHash: `0x${Math.random().toString(16).substr(2, 40)}`,
          tokenAddress,
          timestamp: Date.now(),
        });
      } catch (error) {
        console.error(`Error executing action for ${action.token}:`, error);
        results.push({
          action,
          status: "failed",
          error: error instanceof Error ? error.message : String(error),
          timestamp: Date.now(),
        });
      }
    }

    return results;
  }
}
