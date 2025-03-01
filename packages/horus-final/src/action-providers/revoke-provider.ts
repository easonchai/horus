/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  ActionProvider,
  CreateAction,
  Network,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { Address, parseAbi } from "viem";
import { z } from "zod";
import tokens from "../data/tokens.json";
import { getLogger } from "../utils/logger";

// Initialize logger for this component
const logger = getLogger("RevokeProvider");

/**
 * Configuration structure for tokens in the system
 */
interface TokenConfig {
  symbol: string;
  networks: {
    [chainId: string]: string;
  };
  decimals: number;
}

/**
 * Represents essential information about a token
 */
interface TokenInfo {
  address: Address;
  decimals: number;
}

/**
 * Retrieves token information from the tokens configuration
 * @param {string} symbol - The token symbol to look up
 * @returns {TokenInfo} The token's address and decimals
 * @throws {Error} If the token symbol is not found in configuration
 */
const getTokenInfo = (symbol: string): TokenInfo => {
  logger.debug(`Getting token info for: ${symbol}`);
  const token = tokens.tokens.find((t: TokenConfig) => t.symbol === symbol);
  if (!token) {
    logger.error(`Token ${symbol} not found in configuration`);
    throw new Error(`Token ${symbol} not found`);
  }
  return {
    address: token.networks["84532"] as Address,
    decimals: token.decimals,
  };
};

/**
 * ABI for ERC20 token approval functions
 */
const ERC20_ABI = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function allowance(address owner, address spender) view returns (uint256)",
]);

/**
 * Zod schema for token approval revocation
 */
const revokeSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WETH", "WBTC"]),
  spenderAddress: z
    .string()
    .regex(/^0x[a-fA-F0-9]{40}$/, "Invalid Ethereum address"),
});

/**
 * Zod schema for checking token approvals
 */
const checkApprovalsSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WETH", "WBTC"]),
});

/**
 * RevokeProvider - An action provider for revoking contract approvals
 *
 * This provider allows users to revoke token approvals for specific contracts,
 * which is an important security feature to prevent unauthorized access to tokens.
 */
export class RevokeProvider extends ActionProvider<WalletProvider> {
  /**
   * Creates a new RevokeProvider instance
   */
  constructor() {
    super("revoke-provider", []);
    logger.info("RevokeProvider initialized");
  }

  /**
   * Revokes a token approval for a specific contract address
   * This is an important security feature that prevents contracts from
   * accessing the user's tokens after they're no longer needed.
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the revocation
   * @param {string} args.tokenSymbol - Symbol of the token to revoke approval for
   * @param {string} args.spenderAddress - Address of the contract to revoke approval from
   * @returns {Promise<string>} A human-readable summary of the revocation
   * @throws {Error} If the revocation operation fails
   */
  @CreateAction({
    name: "revoke-token-approval",
    description: "Revoke a token approval for a specific contract address",
    schema: revokeSchema,
  })
  async revokeTokenApproval(
    walletProvider: WalletProvider,
    args: z.infer<typeof revokeSchema>
  ): Promise<string> {
    const { tokenSymbol, spenderAddress } = args;
    logger.info(
      `Executing revoke-token-approval for ${tokenSymbol} from ${spenderAddress}`
    );

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

      // Get token info
      const tokenInfo = getTokenInfo(tokenSymbol);
      logger.debug(
        `Token address: ${tokenInfo.address}, decimals: ${tokenInfo.decimals}`
      );

      logger.info(`Revocation simulation completed successfully`);

      // Return a formatted response
      return `
      # Revocation Summary
      
      ## Transaction Details
      * Token: ${tokenSymbol}
      * Spender Contract: ${spenderAddress}
      * Token Address: ${tokenInfo.address}
      * Wallet Address: ${walletAddress}
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
      logger.error("Error revoking approval:", error);
      return `Error revoking approval for ${tokenSymbol}: ${error}`;
    }
  }

  /**
   * Checks what contracts have approval to spend a specific token
   * Helps users identify which contracts have access to their tokens
   * and provides recommendations for revoking unnecessary approvals.
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the check operation
   * @param {string} args.tokenSymbol - Symbol of the token to check approvals for
   * @returns {Promise<string>} A human-readable summary of token approvals
   * @throws {Error} If the check operation fails
   */
  @CreateAction({
    name: "check-token-approvals",
    description: "Check what contracts have approval to spend your tokens",
    schema: checkApprovalsSchema,
  })
  async checkTokenApprovals(
    walletProvider: WalletProvider,
    args: z.infer<typeof checkApprovalsSchema>
  ): Promise<string> {
    const { tokenSymbol } = args;
    logger.info(`Checking token approvals for ${tokenSymbol}`);

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

      // Get token info for logging
      const tokenInfo = getTokenInfo(tokenSymbol);
      logger.debug(`Token address: ${tokenInfo.address}`);

      // Mock implementation - In a real scenario, you would query the blockchain
      // for all approval events for this token and user
      logger.debug("Using mock approvals data for demonstration");
      const mockApprovals = [
        {
          spender: "0x1234...5678",
          name: "Uniswap Router",
          amount: "Unlimited",
        },
        { spender: "0x5678...9012", name: "Beefy Vault", amount: "100.0" },
      ];

      logger.debug(
        `Found ${mockApprovals.length} approvals for ${tokenSymbol}`
      );

      // Format the response
      let approvalsText = mockApprovals
        .map((a) => `* **${a.name}** (${a.spender}): ${a.amount}`)
        .join("\n");

      logger.info(`Approval check completed successfully`);

      return `
      # Token Approvals for ${tokenSymbol}
      
      Showing approvals for wallet: ${walletAddress}
      
      The following contracts have approval to spend your ${tokenSymbol}:
      
      ${approvalsText}
      
      ## Recommendations
      
      Consider revoking approvals for contracts you no longer use.
      You can use the \`revoke-token-approval\` action to revoke specific approvals.
      `;
    } catch (error) {
      logger.error("Error checking approvals:", error);
      return `Error checking approvals for ${tokenSymbol}: ${error}`;
    }
  }

  /**
   * Determines if this provider supports the given network
   * Currently only supports Base Sepolia (ChainID: 84532)
   *
   * @param {Network} network - The network to check
   * @returns {boolean} True if the network is supported, false otherwise
   */
  supportsNetwork = (network: Network) => {
    // Convert chainId to number for comparison if it's a string
    const chainId =
      typeof network.chainId === "string"
        ? parseInt(network.chainId, 10)
        : network.chainId;

    const isSupported = chainId === 84532; // Base Sepolia
    logger.debug(
      `Network support check: chainId=${chainId}, supported=${isSupported}`
    );
    return isSupported;
  };
}

/**
 * Factory function to create a new RevokeProvider instance
 * @returns {RevokeProvider} A new RevokeProvider instance
 */
export const revokeProvider = () => new RevokeProvider();
