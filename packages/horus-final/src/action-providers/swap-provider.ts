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
import dependencyGraphData from "../data/dependency_graph.json";
import protocols from "../data/protocols.json";
import tokens from "../data/tokens.json";
import { getLogger } from "../utils/logger";

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
  address: Address;
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
    address: token.networks["84532"] as Address,
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
    | Address
    | undefined,
  FEE_TIER: 500, // 0.05%
};

if (!UNISWAP.ROUTER) {
  logger.warn("Uniswap router address not found in protocol configuration");
}

/**
 * ABI for the Uniswap V3 Router
 */
const ROUTER_ABI = parseAbi([
  "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
]);

/**
 * ABI for ERC20 token functions
 */
const ERC20_ABI = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
]);

/**
 * Zod schema for swap action input validation
 */
const swapSchema = z.object({
  fromToken: z.enum(["USDC", "USDT"]),
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
    const { fromToken } = args;
    logger.info(`Executing swap-max-balance for ${fromToken}`);

    try {
      // Get user's wallet address from the wallet provider
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get token info
      const tokenIn = getTokenInfo(fromToken);
      const tokenOut = getTokenInfo(fromToken === "USDC" ? "USDT" : "USDC");

      logger.debug(`Token in: ${fromToken}, address: ${tokenIn.address}`);
      logger.debug(
        `Token out: ${fromToken === "USDC" ? "USDT" : "USDC"}, address: ${
          tokenOut.address
        }`
      );

      logger.info(`Swap simulation completed successfully`);

      // Return a formatted response
      return `
      # Swap Transaction Summary
      
      ## Transaction Details
      * From Token: ${fromToken}
      * To Token: ${fromToken === "USDC" ? "USDT" : "USDC"}
      * Amount: [Max Balance]
      * User Address: ${userAddress}
      * Status: Simulated

      ## Notes
      This is a simulated swap. In a real implementation, this would:
      1. Check token balance using the wallet provider
      2. Approve the router to spend tokens
      3. Execute the swap transaction
      
      The wallet provider has been successfully connected.
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
