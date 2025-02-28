/* eslint-disable @typescript-eslint/no-explicit-any */
import { ActionProvider, Network, WalletProvider } from "@coinbase/agentkit";
import { ethers } from "ethers";
import protocols from "../../../../config/protocols.json";
import tokens from "../../../../config/tokens.json";
import { DependencyGraphService } from "../services/dependency-graph-service";

interface SwapParams {
  tokenIn: string;
  tokenOut: string;
  fee: number;
  recipient: string;
  amountIn: string;
  amountOutMinimum: string;
  sqrtPriceLimitX96: string;
}

interface TokenInfo {
  address: string;
  decimals: number;
}

// Get token info from config
const getTokenInfo = (symbol: string): TokenInfo => {
  const token = tokens.tokens.find((t) => t.symbol === symbol);
  if (!token) throw new Error(`Token ${symbol} not found`);
  return {
    address: token.networks["84532"],
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

// Get Uniswap addresses from protocols.json
const UNISWAP = {
  ROUTER: protocols.protocols.find((p) => p.name === "UniswapV3")?.chains[
    "84532"
  ].swapRouter02,
  FEE_TIER: 500, // 0.05%
};

const ROUTER_ABI = [
  "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
];

const ERC20_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
];

class SwapProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("swap-provider", []);
  }

  supportsNetwork = (network: Network) => network.chainId === 84532; // Base Sepolia

  // Get token balance
  private async getTokenBalance(tokenAddress: string, userAddress: string) {
    const provider = await this.walletProvider.getProvider();
    const tokenContract = new ethers.Contract(
      tokenAddress,
      ERC20_ABI,
      provider
    );
    return await tokenContract.balanceOf(userAddress);
  }

  // Approve router to spend tokens
  private async approveRouter(tokenAddress: string, amount: string) {
    const provider = await this.walletProvider.getProvider();
    const signer = await this.walletProvider.getSigner();
    const tokenContract = new ethers.Contract(
      tokenAddress,
      ERC20_ABI,
      provider
    );

    if (!UNISWAP.ROUTER) throw new Error("Uniswap router address not found");
    const tx = ((await tokenContract) as any)
      .connect(signer)
      .approve(UNISWAP.ROUTER, amount);
    await tx.wait();
  }

  // Swap all USDT to USDC or vice versa
  async swapMaxBalance(fromToken: "USDC" | "USDT") {
    const provider = await this.walletProvider.getProvider();
    const signer = await this.walletProvider.getSigner();
    const userAddress = await signer.getAddress();

    // Get token info from config
    const tokenIn = getTokenInfo(fromToken);
    const tokenOut = getTokenInfo(fromToken === "USDC" ? "USDT" : "USDC");

    // Get swap info from dependency graph
    const swapInfo = getSwapInfo(fromToken);
    if (!swapInfo) throw new Error(`No swap info found for ${fromToken}`);

    // Get max balance
    const balance = await this.getTokenBalance(tokenIn.address, userAddress);
    if (balance.isZero()) {
      throw new Error(`No ${fromToken} balance to swap`);
    }

    // Approve router
    await this.approveRouter(tokenIn.address, balance.toString());

    // Prepare swap params
    const params: SwapParams = {
      tokenIn: tokenIn.address,
      tokenOut: tokenOut.address,
      fee: UNISWAP.FEE_TIER,
      recipient: userAddress,
      amountIn: balance.toString(),
      amountOutMinimum: "0", // Be careful with this in production!
      sqrtPriceLimitX96: "0",
    };

    // Execute swap
    if (!UNISWAP.ROUTER) throw new Error("Uniswap router address not found");
    const router = new ethers.Contract(UNISWAP.ROUTER, ROUTER_ABI, provider);
    const tx = ((await router) as any).connect(signer).exactInputSingle(params);
    await tx.wait();

    return tx;
  }
}

export default SwapProvider;
