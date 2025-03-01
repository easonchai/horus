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
import protocols from "../data/protocols.json";

// Extract protocol configurations
const beefyProtocol = protocols.protocols.find((p: any) => p.name === "Beefy");

const uniswapProtocol = protocols.protocols.find(
  (p: any) => p.name === "UniswapV3"
);

// Define constants for protocol addresses
const PROTOCOL_ADDRESSES = {
  BEEFY: {
    USDC_USDT_VAULT: beefyProtocol?.chains?.["84532"]?.[
      "beefyUSDC-USDT-Vault"
    ] as Address | undefined,
    WBTC_EIGEN_VAULT: beefyProtocol?.chains?.["84532"]?.[
      "beefyWBTC-EIGEN-Vault"
    ] as Address | undefined,
    USDC_EIGEN_VAULT: beefyProtocol?.chains?.["84532"]?.[
      "beefyUSDC-EIGEN-Vault"
    ] as Address | undefined,
  },
  UNISWAP: {
    POSITION_MANAGER: uniswapProtocol?.chains?.["84532"]
      ?.nonfungiblePositionManager as Address | undefined,
  },
};

// ABI definitions for protocol interactions
const BEEFY_VAULT_ABI = parseAbi([
  "function withdraw(uint256 tokenId) external",
  "function balanceOf(address account) view returns (uint256)",
]);

const UNISWAP_POSITION_MANAGER_ABI = parseAbi([
  "function decreaseLiquidity(uint256 tokenId, uint128 liquidity, uint256 amount0Min, uint256 amount1Min, uint256 deadline) external returns (uint256, uint256)",
  "function collect(uint256 tokenId, address recipient, uint128 amount0Max, uint128 amount1Max) external returns (uint256, uint256)",
  "function positions(uint256 tokenId) external view returns (uint96 nonce, address operator, address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint128 liquidity, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, uint128 tokensOwed0, uint128 tokensOwed1)",
]);

// Define schemas for withdrawal actions
const beefyWithdrawSchema = z.object({
  vaultType: z.enum(["USDC-USDT", "WBTC-EIGEN", "USDC-EIGEN"]),
  tokenId: z.number().int().positive(),
});

const uniswapWithdrawSchema = z.object({
  positionId: z.number().int().positive(),
  percentage: z.number().min(0).max(100).default(100),
});

// Define schema for emergency withdrawal
const emergencyWithdrawSchema = z.object({
  reason: z.string().optional(),
  prioritizeSafety: z.boolean().default(true),
});

/**
 * WithdrawalProvider - An action provider for withdrawing assets from DeFi protocols
 *
 * This provider allows users to withdraw their funds from various DeFi protocols,
 * including Beefy vaults and Uniswap liquidity positions.
 */
export class WithdrawalProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("withdrawal-provider", []);
  }

  @CreateAction({
    name: "withdraw-from-beefy",
    description: "Withdraw funds from a Beefy vault",
    schema: beefyWithdrawSchema,
  })
  async withdrawFromBeefy(
    walletProvider: WalletProvider,
    args: z.infer<typeof beefyWithdrawSchema>
  ): Promise<string> {
    const { vaultType, tokenId } = args;

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();

      // Map the vault type to the specific vault address
      let vaultAddress: Address | undefined;
      let vaultName: string;

      switch (vaultType) {
        case "USDC-USDT":
          vaultAddress = PROTOCOL_ADDRESSES.BEEFY.USDC_USDT_VAULT;
          vaultName = "USDC-USDT Vault";
          break;
        case "WBTC-EIGEN":
          vaultAddress = PROTOCOL_ADDRESSES.BEEFY.WBTC_EIGEN_VAULT;
          vaultName = "WBTC-EIGEN Vault";
          break;
        case "USDC-EIGEN":
          vaultAddress = PROTOCOL_ADDRESSES.BEEFY.USDC_EIGEN_VAULT;
          vaultName = "USDC-EIGEN Vault";
          break;
      }

      if (!vaultAddress) {
        return `Error: Vault address not found for ${vaultType}`;
      }

      // In a real implementation, you would:
      // 1. Check if the user has a position in the vault
      // 2. Execute the withdrawal transaction
      // 3. Return the result

      // Return a formatted mock response
      return `
      # Withdrawal from Beefy Summary
      
      ## Transaction Details
      * Protocol: Beefy Finance
      * Vault: ${vaultName}
      * Vault Address: ${vaultAddress}
      * Token ID: ${tokenId}
      * Wallet Address: ${walletAddress}
      * Status: Simulated
      
      ## Notes
      This withdrawal would remove your funds from the Beefy vault.
      In a real implementation, this would:
      
      1. Connect to the vault contract using your wallet provider
      2. Call the withdraw function with your token ID
      3. Confirm the transaction on the blockchain
      
      ## Security Considerations
      Withdrawing funds during times of high volatility might result in slippage.
      Consider the market conditions before executing this withdrawal.
      `;
    } catch (error) {
      console.error("Error withdrawing from Beefy:", error);
      return `Error withdrawing from Beefy vault (${vaultType}): ${error}`;
    }
  }

  @CreateAction({
    name: "withdraw-from-uniswap",
    description: "Withdraw liquidity from a Uniswap position",
    schema: uniswapWithdrawSchema,
  })
  async withdrawFromUniswap(
    walletProvider: WalletProvider,
    args: z.infer<typeof uniswapWithdrawSchema>
  ): Promise<string> {
    const { positionId, percentage } = args;

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();

      const positionManagerAddress =
        PROTOCOL_ADDRESSES.UNISWAP.POSITION_MANAGER;

      if (!positionManagerAddress) {
        return "Error: Uniswap Position Manager address not found";
      }

      // In a real implementation, you would:
      // 1. Get the position details
      // 2. Calculate the liquidity to withdraw based on percentage
      // 3. Execute the decreaseLiquidity transaction
      // 4. Execute the collect transaction to get the tokens

      // Calculate how much liquidity to withdraw
      const liquidityPercentage = percentage === 100 ? "all" : `${percentage}%`;

      // Return a formatted mock response
      return `
      # Uniswap Liquidity Withdrawal Summary
      
      ## Transaction Details
      * Protocol: Uniswap V3
      * Position ID: ${positionId}
      * Withdraw Amount: ${liquidityPercentage} of position
      * Position Manager: ${positionManagerAddress}
      * Wallet Address: ${walletAddress}
      * Status: Simulated
      
      ## Process
      This withdrawal would execute in two steps:
      
      1. Call \`decreaseLiquidity\` to remove ${liquidityPercentage} of your liquidity
      2. Call \`collect\` to receive the withdrawn tokens
      
      ## Estimated Returns
      In a real implementation, this would calculate and show:
      * Estimated Token A: X.XXX
      * Estimated Token B: Y.YYY
      * Collected Fees: Z.ZZZ
      
      ## Security Considerations
      Withdrawing liquidity during high volatility periods may result in suboptimal returns.
      Consider market conditions before proceeding.
      `;
    } catch (error) {
      console.error("Error withdrawing from Uniswap:", error);
      return `Error withdrawing from Uniswap position ${positionId}: ${error}`;
    }
  }

  @CreateAction({
    name: "emergency-withdraw-all",
    description:
      "Emergency withdrawal from all connected protocols in case of security threat",
    schema: emergencyWithdrawSchema,
  })
  async emergencyWithdrawAll(
    walletProvider: WalletProvider,
    args: z.infer<typeof emergencyWithdrawSchema>
  ): Promise<string> {
    const { reason, prioritizeSafety } = args;

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();

      // In a real implementation, you would:
      // 1. Scan for all user positions across protocols
      // 2. Execute withdrawals in order of priority (set by prioritizeSafety flag)
      // 3. Report on the results

      return `
      # 🚨 EMERGENCY WITHDRAWAL INITIATED 🚨
      
      ## Withdrawal Reason
      ${reason || "Security threat detected"}
      
      ## Wallet Details
      Executing emergency withdrawal for wallet: ${walletAddress}
      
      ## Protocols Targeted
      * Beefy Finance Vaults
      * Uniswap V3 Positions
      
      ## Strategy
      ${
        prioritizeSafety
          ? "Prioritizing safety over maximum returns. This may result in some slippage but reduces time exposure to potential threats."
          : "Balancing safety and returns. This may take longer but will attempt to minimize slippage and losses."
      }
      
      ## Status
      This is a simulated emergency withdrawal.
      
      In a real implementation, this would:
      1. Identify all your positions across supported protocols
      2. Execute withdrawals in priority order using your connected wallet
      3. Confirm funds are secured in your wallet
      
      ## Security Notes
      Emergency withdrawals should only be used during legitimate security threats.
      This action may incur higher gas fees and potential slippage.
      `;
    } catch (error) {
      console.error("Error performing emergency withdrawal:", error);
      return `Error performing emergency withdrawal: ${error}`;
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

export const withdrawalProvider = () => new WithdrawalProvider();
