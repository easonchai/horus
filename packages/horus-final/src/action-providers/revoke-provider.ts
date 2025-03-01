/* eslint-disable @typescript-eslint/no-explicit-any */
import { ActionProvider, CreateAction, Network } from "@coinbase/agentkit";
import "reflect-metadata";
import { Address, parseAbi } from "viem";
import { z } from "zod";
import tokens from "../data/tokens.json";

interface TokenConfig {
  symbol: string;
  networks: {
    [chainId: string]: string;
  };
  decimals: number;
}

interface TokenInfo {
  address: Address;
  decimals: number;
}

// Get token info from config
const getTokenInfo = (symbol: string): TokenInfo => {
  const token = tokens.tokens.find((t: TokenConfig) => t.symbol === symbol);
  if (!token) throw new Error(`Token ${symbol} not found`);
  return {
    address: token.networks["84532"] as Address,
    decimals: token.decimals,
  };
};

// ERC20 ABI for approval functions
const ERC20_ABI = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function allowance(address owner, address spender) view returns (uint256)",
]);

// Define schema for contract revocation
const revokeSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WETH", "WBTC"]),
  spenderAddress: z
    .string()
    .regex(/^0x[a-fA-F0-9]{40}$/, "Invalid Ethereum address"),
});

// Define schema for checking token approvals
const checkApprovalsSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WETH", "WBTC"]),
});

/**
 * RevokeProvider - An action provider for revoking contract approvals
 *
 * This provider allows users to revoke token approvals for specific contracts,
 * which is an important security feature to prevent unauthorized access to tokens.
 */
export class RevokeProvider extends ActionProvider {
  constructor() {
    super("revoke-provider", []);
  }

  @CreateAction({
    name: "revoke-token-approval",
    description: "Revoke a token approval for a specific contract address",
    schema: revokeSchema,
  })
  async revokeTokenApproval(
    args: z.infer<typeof revokeSchema>
  ): Promise<string> {
    const { tokenSymbol, spenderAddress } = args;

    try {
      // In a real implementation, we would get the wallet provider from the context
      // Using mock implementation for demonstration
      const walletAddress = "0x123..."; // Mock address

      // Get token info
      const tokenInfo = getTokenInfo(tokenSymbol);

      // Return a formatted response
      return `
      # Revocation Summary
      
      ## Transaction Details
      * Token: ${tokenSymbol}
      * Spender Contract: ${spenderAddress}
      * Token Address: ${tokenInfo.address}
      * Status: Simulated
      
      ## Security Notes
      This revocation would set the allowance to zero, effectively removing 
      the contract's permission to spend your tokens. In a real implementation, 
      this would:
      
      1. Check current allowance
      2. Call the token's approve() function with value 0
      3. Verify transaction success
      
      ## Why Revoke?
      Revoking permissions helps protect your assets from potential exploits 
      by removing access rights from protocols you no longer use.
      `;
    } catch (error) {
      console.error("Error revoking approval:", error);
      return `Error revoking approval for ${tokenSymbol}: ${error}`;
    }
  }

  @CreateAction({
    name: "check-token-approvals",
    description: "Check what contracts have approval to spend your tokens",
    schema: checkApprovalsSchema,
  })
  async checkTokenApprovals(
    args: z.infer<typeof checkApprovalsSchema>
  ): Promise<string> {
    const { tokenSymbol } = args;

    try {
      // Mock implementation - In a real scenario, you would query the blockchain
      // for all approval events for this token and user
      const mockApprovals = [
        {
          spender: "0x1234...5678",
          name: "Uniswap Router",
          amount: "Unlimited",
        },
        { spender: "0x5678...9012", name: "Beefy Vault", amount: "100.0" },
      ];

      // Format the response
      let approvalsText = mockApprovals
        .map((a) => `* **${a.name}** (${a.spender}): ${a.amount}`)
        .join("\n");

      return `
      # Token Approvals for ${tokenSymbol}
      
      The following contracts have approval to spend your ${tokenSymbol}:
      
      ${approvalsText}
      
      ## Recommendations
      
      Consider revoking approvals for contracts you no longer use.
      You can use the \`revoke-token-approval\` action to revoke specific approvals.
      `;
    } catch (error) {
      console.error("Error checking approvals:", error);
      return `Error checking approvals for ${tokenSymbol}: ${error}`;
    }
  }

  supportsNetwork = (network: Network) => {
    // Convert chainId to number for comparison if it's a string
    const chainId =
      typeof network.chainId === "string"
        ? parseInt(network.chainId, 10)
        : network.chainId;
    return chainId === 84532; // Base Sepolia
  };

  // Helper method to get the wallet provider
  private getWalletProvider(): any {
    // This would need to be implemented based on how AgentKit provides wallet providers
    // For now, we'll return null and handle it later
    return (this as any).walletProvider;
  }
}

export const revokeProvider = () => new RevokeProvider();
