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

// Create a DependencyGraphService from the JSON data
class DependencyGraphService {
  static getSwapFunctions(symbol: string) {
    const derivative = dependencyGraphData.dependencies.find(
      (dep: any) => dep.derivativeSymbol === symbol
    );
    return derivative?.swapFunctions || [];
  }
}

interface TokenInfo {
  address: Address;
  decimals: number;
}

interface TokenConfig {
  symbol: string;
  networks: {
    [chainId: string]: string;
  };
  decimals: number;
}

// Update interface to match actual structure in protocols.json
interface ProtocolConfig {
  name: string;
  chains: {
    [chainId: string]: {
      [key: string]: string;
    };
  };
  abis: any;
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

// Get swap info from dependency graph
const getSwapInfo = (symbol: string) => {
  const swapFunctions = DependencyGraphService.getSwapFunctions(symbol);
  if (!swapFunctions || swapFunctions.length === 0) {
    throw new Error(`No swap functions found for ${symbol}`);
  }
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

const ROUTER_ABI = parseAbi([
  "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
]);

const ERC20_ABI = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
]);

// Define the schema for swap
const swapSchema = z.object({
  fromToken: z.enum(["USDC", "USDT"]),
});

export class SwapProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("swap-provider", []);
  }

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

    try {
      // Get user's wallet address from the wallet provider
      const userAddress = await walletProvider.getAddress();

      // Get token info
      const tokenIn = getTokenInfo(fromToken);
      const tokenOut = getTokenInfo(fromToken === "USDC" ? "USDT" : "USDC");

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
      console.error("Error executing swap:", error);
      return `Error swapping ${fromToken}: ${error}`;
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
}

export const swapProvider = () => new SwapProvider();
