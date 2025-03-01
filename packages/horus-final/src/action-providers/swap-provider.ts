/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  ActionProvider,
  CreateAction,
  Network,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { getLogger } from "../utils/logger";
import dependencyGraphData from "../data/dependency_graph.json";
import protocols from "../data/protocols.json";
import tokens from "../data/tokens.json";
import { z } from "zod";
import { Wallet } from "../wallet";

// Initialize logger for this component
const logger = getLogger("SwapProvider");

/**
 * Provides utility methods for handling token swap dependency graphs.
 * Used to determine available swap functions for a given token.
 */
class DependencyGraphService {
  /**
   * Retrieves swap functions available for a specific token
   * @param {string} symbol - The token symbol (e.g., "USDC", "USDT")
   * @returns {Array} Array of swap functions for the specified token
   */
  static getSwapFunctions(symbol: string) {
    logger.debug(`Looking up swap functions for token: ${symbol}`);
    const derivative = dependencyGraphData.dependencies.find(
      (dep: any) => dep.derivativeSymbol === symbol
    );
    if (!derivative) {
      logger.warn(`No derivative found for token symbol: ${symbol}`);
    }
    return derivative?.swapFunctions || [];
  }
}

/**
 * Represents essential information about a token
 */
interface TokenInfo {
  address: string;
  decimals: number;
}

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
 * Configuration structure for DeFi protocols in the system
 */
interface ProtocolConfig {
  name: string;
  chains: {
    [chainId: string]: {
      [key: string]: string;
    };
  };
  abis: any;
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
 * Retrieves swap function information for a token from the dependency graph
 * @param {string} symbol - The token symbol to look up
 * @returns {any} The first swap function found for the token
 * @throws {Error} If no swap functions are found for the token
 */
const getSwapInfo = (symbol: string) => {
  logger.debug(`Getting swap info for: ${symbol}`);
  const swapFunctions = DependencyGraphService.getSwapFunctions(symbol);
  if (!swapFunctions || swapFunctions.length === 0) {
    logger.error(`No swap functions found for ${symbol}`);
    throw new Error(`No swap functions found for ${symbol}`);
  }
  logger.debug(`Found ${swapFunctions.length} swap functions for ${symbol}`);
  return swapFunctions[0];
};

// Get Uniswap protocol from protocols.json
const uniswapProtocol = protocols.protocols.find(
  (p: any) => p.name === "UniswapV3"
);

// Make sure we have a default value in case UniswapV3 is not found
const UNISWAP = {
  ROUTER: uniswapProtocol?.chains?.["84532"]?.swapRouter02 as
    | string
    | undefined,
  FEE_TIER: 500, // 0.05%
};

if (!UNISWAP.ROUTER) {
  logger.warn("Uniswap router address not found in protocol configuration");
}

/**
 * ABI for the Uniswap V3 Router
 */
const ROUTER_ABI = [
  "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
];

/**
 * ABI for ERC20 token functions
 */
const ERC20_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
];

/**
 * Zod schema for swap action input validation
 */
const swapSchema = z.object({
  fromToken: z.enum(["USDC", "USDT"]).describe("Token to swap from"),
  amount: z.number().describe("Amount of tokens to swap"),
});

/**
 * Provider for token swap operations
 * Enables swapping stablecoins (USDC to USDT or vice versa) via Uniswap
 */
export class SwapProvider extends ActionProvider<WalletProvider> {
  /**
   * Creates a new SwapProvider instance
   */
  constructor() {
    super("swap-provider", []);
    logger.info("SwapProvider initialized");
  }

  /**
   * Swaps the maximum balance of a token for another token
   * Currently supports swapping between USDC and USDT
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the swap operation
   * @param {string} args.fromToken - The token to swap from (USDC or USDT)
   * @returns {Promise<string>} A human-readable summary of the swap operation
   * @throws {Error} If the swap operation fails
   */
  @CreateAction({
    name: "swap-max-balance",
    description:
      "Swap the maximum balance of a token for another token (USDC to USDT or vice versa)",
    schema: swapSchema,
  })
  async swapMaxBalance(
    walletProvider: WalletProvider,
    args: z.infer<typeof swapSchema>
  ): Promise<string> {
    const { fromToken, amount } = args;
    logger.info(
      `Executing swap-max-balance for ${fromToken}, amount: ${amount}`
    );

    try {
      // Validate Uniswap router address
      if (!UNISWAP.ROUTER) {
        throw new Error("Uniswap router address not found in configuration");
      }

      // Get user's wallet address from the wallet provider
      // const wallet = new Wallet();
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get token info
      const tokenIn = getTokenInfo(fromToken);
      const tokenOut = getTokenInfo(fromToken === "USDC" ? "USDT" : "USDC");

      // Get swap info from dependency graph
      const swapInfo = getSwapInfo(fromToken);
      logger.debug(
        `Using swap function: ${swapInfo.functionName} from ${swapInfo.protocol}`
      );

      logger.debug(`Token in: ${fromToken}, address: ${tokenIn.address}`);
      logger.debug(
        `Token out: ${fromToken === "USDC" ? "USDT" : "USDC"}, address: ${
          tokenOut.address
        }`
      );

      // Convert amount to token units with decimals
      const amountInWei = BigInt(amount * 10 ** tokenIn.decimals);
      logger.debug(`Amount in wei: ${amountInWei}`);

      // Step 2: Approve the router to spend tokens
      logger.info(
        `Approving ${UNISWAP.ROUTER} to spend ${amountInWei} ${fromToken}`
      );

      // Approve the router to spend tokens
      const wallet = new Wallet();
      const { getPublicClient, getWalletClient } = wallet;
      const publicClient = getPublicClient();
      const walletClient = getWalletClient();

      const approvalTxHash = await publicClient.writeContract({
        address: tokenIn.address,
        abi: ERC20_ABI,
        functionName: "approve",
        args: [UNISWAP.ROUTER, amountInWei.toString()],
        chainId: 84532, // Base Sepolia
      });

      logger.info(`Approval transaction hash: ${approvalTxHash}`);

      // Wait for approval transaction to be mined
      const approvalReceipt = await publicClient.waitForTransactionReceipt({
        hash: approvalTxHash,
      });

      logger.info(`Approval transaction confirmed: ${approvalReceipt.status}`);

      if (approvalReceipt.status !== "success") {
        throw new Error("Token approval failed");
      }

      // Step 3: Execute the swap
      // Calculate minimum amount out (with 0.5% slippage)
      const amountOutMinimum = (amountInWei * BigInt(995)) / BigInt(1000);

      // Prepare swap parameters
      const swapParams = {
        tokenIn: tokenIn.address,
        tokenOut: tokenOut.address,
        fee: UNISWAP.FEE_TIER,
        recipient: userAddress,
        amountIn: amountInWei.toString(),
        amountOutMinimum: amountOutMinimum.toString(),
        sqrtPriceLimitX96: BigInt(0).toString(), // No price limit
      };

      logger.debug(
        `Swap parameters: ${JSON.stringify(swapParams, (_, v) =>
          typeof v === "bigint" ? v.toString() : v
        )}`
      );

      // Execute the swap transaction
      const swapTxHash = await publicClient.writeContract({
        address: UNISWAP.ROUTER,
        abi: ROUTER_ABI,
        functionName: "exactInputSingle",
        args: [swapParams],
        chainId: 84532, // Base Sepolia
      });

      logger.info(`Swap transaction hash: ${swapTxHash}`);

      // Wait for swap transaction to be mined
      const swapReceipt = await publicClient.waitForTransactionReceipt({
        hash: swapTxHash,
      });

      logger.info(`Swap transaction confirmed: ${swapReceipt.status}`);

      if (swapReceipt.status !== "success") {
        throw new Error("Swap transaction failed");
      }

      // Return a formatted response
      return `
      # Swap Transaction Summary
      
      ## Transaction Details
      * From Token: ${fromToken}
      * To Token: ${fromToken === "USDC" ? "USDT" : "USDC"}
      * Amount: ${amount} ${fromToken}
      * User Address: ${userAddress}
      * Status: 🟢 Success

      ## Transaction Information
      * Approval TX: [${approvalTxHash}](https://sepolia.basescan.org/tx/${approvalTxHash})
      * Swap TX: [${swapTxHash}](https://sepolia.basescan.org/tx/${swapTxHash})
      * Slippage Protection: 0.5%
      
      Your swap has been successfully completed!
      `;
    } catch (error) {
      logger.error("Error executing swap:", error);
      return `Error swapping ${fromToken}: ${error}`;
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
 * Factory function to create a new SwapProvider instance
 * @returns {SwapProvider} A new SwapProvider instance
 */
export const swapProvider = () => new SwapProvider();
