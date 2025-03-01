/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  ActionProvider,
  CreateAction,
  Network,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { z } from "zod";
import tokens from "../data/tokens.json";
import { getLogger } from "../utils/logger";
import { baseSepolia } from "viem/chains";

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
  address: string;
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
    address: token.networks["84532"],
    decimals: token.decimals,
  };
};

/**
 * ABI for ERC20 token approval functions
 */
const ERC20_ABI = [
  {
    name: "balanceOf",
    type: "function",
    stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ type: "uint256" }],
  },
  {
    name: "approve",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ type: "bool" }],
  },
  {
    name: "allowance",
    type: "function",
    stateMutability: "view",
    inputs: [
      { name: "owner", type: "address" },
      { name: "spender", type: "address" },
    ],
    outputs: [{ type: "uint256" }],
  },
];

/**
 * Zod schema for token approval revocation
 */
const revokeSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WBTC", "EIGEN"]),
  spenderAddress: z
    .string()
    .regex(/^0x[a-fA-F0-9]{40}$/, "Invalid Ethereum address"),
});

/**
 * Zod schema for checking token approvals
 */
const checkApprovalsSchema = z.object({
  tokenSymbol: z.enum(["USDC", "USDT", "WBTC", "EIGEN"]),
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
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get token info
      const tokenInfo = getTokenInfo(tokenSymbol);
      logger.debug(
        `Token address: ${tokenInfo.address}, decimals: ${tokenInfo.decimals}`
      );

      // Import the wallet
      const { Wallet } = await import("../wallet");
      const wallet = new Wallet();

      // Make sure wallet is initialized
      wallet.initialize();

      const publicClient = wallet.publicClient;
      const walletClient = wallet.walletClient;

      if (!walletClient || !publicClient) {
        throw new Error("Wallet client not initialized");
      }

      // Get the current allowance
      const allowance = await publicClient.readContract({
        address: tokenInfo.address as `0x${string}`,
        abi: ERC20_ABI,
        functionName: "allowance",
        args: [userAddress as `0x${string}`, spenderAddress as `0x${string}`],
      });

      logger.info(`Current allowance: ${allowance}`);

      // Get the transaction count for nonce
      const transactionCount = await publicClient.getTransactionCount({
        address: userAddress as `0x${string}`,
      });

      // Set approval to zero to revoke
      const revokeTxHash = await walletClient.writeContract({
        address: tokenInfo.address as `0x${string}`,
        abi: ERC20_ABI,
        functionName: "approve",
        args: [spenderAddress as `0x${string}`, BigInt(0)],
        chain: baseSepolia,
        nonce: transactionCount,
      } as any);

      logger.info(`Revocation transaction hash: ${revokeTxHash}`);

      // Wait for transaction to be mined
      const revokeReceipt = await publicClient.waitForTransactionReceipt({
        hash: revokeTxHash,
      });

      logger.info(`Revocation transaction confirmed: ${revokeReceipt.status}`);

      if (revokeReceipt.status !== "success") {
        throw new Error("Revocation transaction failed");
      }

      // Return a formatted response
      return `
      # Revocation Summary
      
      ## Transaction Details
      * Token: ${tokenSymbol}
      * Spender Contract: ${spenderAddress}
      * Token Address: ${tokenInfo.address}
      * Wallet Address: ${userAddress}
      * Status: 🟢 Success
      
      ## Transaction Information
      * Revocation TX: [${revokeTxHash}](https://sepolia.basescan.org/tx/${revokeTxHash})
      * Previous Allowance: ${allowance.toString()}
      * New Allowance: 0
      
      ## Security Notes
      You have successfully revoked permission for this contract to spend your tokens.
      This helps protect your assets from potential exploits by removing access rights
      from protocols you no longer use.
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
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get token info for logging
      const tokenInfo = getTokenInfo(tokenSymbol);
      logger.debug(`Token address: ${tokenInfo.address}`);

      // Import the wallet
      const { Wallet } = await import("../wallet");
      const wallet = new Wallet();

      // Make sure wallet is initialized
      wallet.initialize();

      const publicClient = wallet.publicClient;

      if (!publicClient) {
        throw new Error("Public client not initialized");
      }

      // Known contract addresses to check for approvals
      // In a real implementation, you would query events to find all approvals
      const knownContracts = [
        {
          address: "0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4", // Uniswap Router
          name: "Uniswap Router",
        },
        {
          address: "0x4200000000000000000000000000000000000006", // WETH
          name: "WETH Contract",
        },
      ];

      // Check approvals for each known contract
      const approvals = await Promise.all(
        knownContracts.map(async (contract) => {
          try {
            const allowance = await publicClient.readContract({
              address: tokenInfo.address as `0x${string}`,
              abi: ERC20_ABI,
              functionName: "allowance",
              args: [
                userAddress as `0x${string}`,
                contract.address as `0x${string}`,
              ],
            });

            return {
              spender: contract.address,
              name: contract.name,
              amount: allowance.toString(),
              hasApproval: allowance > BigInt(0),
            };
          } catch (error) {
            logger.error(
              `Error checking allowance for ${contract.name}:`,
              error
            );
            return {
              spender: contract.address,
              name: contract.name,
              amount: "Error checking",
              hasApproval: false,
            };
          }
        })
      );

      // Filter to only show contracts with approvals
      const activeApprovals = approvals.filter((a) => a.hasApproval);

      logger.debug(
        `Found ${activeApprovals.length} active approvals for ${tokenSymbol}`
      );

      // Format the response
      let approvalsText =
        activeApprovals.length > 0
          ? activeApprovals
              .map((a) => `* **${a.name}** (${a.spender}): ${a.amount}`)
              .join("\n")
          : "* No active approvals found";

      logger.info(`Approval check completed successfully`);

      return `
      # Token Approvals for ${tokenSymbol}
      
      Showing approvals for wallet: ${userAddress}
      
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
