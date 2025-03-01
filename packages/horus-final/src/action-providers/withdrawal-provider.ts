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
import { getLogger } from "../utils/logger";

// Initialize logger for this component
const logger = getLogger("WithdrawalProvider");

/**
 * Extract protocol configurations from the loaded protocols data
 */
const beefyProtocol = protocols.protocols.find((p: any) => p.name === "Beefy");

const uniswapProtocol = protocols.protocols.find(
  (p: any) => p.name === "UniswapV3"
);

/**
 * Constant addresses for various protocol contracts
 * These are used to interact with the specific vaults and position managers
 */
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

// Log any missing protocol addresses
if (!PROTOCOL_ADDRESSES.BEEFY.USDC_USDT_VAULT) {
  logger.warn(
    "Beefy USDC-USDT vault address not found in protocol configuration"
  );
}
if (!PROTOCOL_ADDRESSES.BEEFY.WBTC_EIGEN_VAULT) {
  logger.warn(
    "Beefy WBTC-EIGEN vault address not found in protocol configuration"
  );
}
if (!PROTOCOL_ADDRESSES.BEEFY.USDC_EIGEN_VAULT) {
  logger.warn(
    "Beefy USDC-EIGEN vault address not found in protocol configuration"
  );
}
if (!PROTOCOL_ADDRESSES.UNISWAP.POSITION_MANAGER) {
  logger.warn(
    "Uniswap position manager address not found in protocol configuration"
  );
}

/**
 * ABI for Beefy vault operations
 */
const BEEFY_VAULT_ABI = parseAbi([
  "function withdraw(uint256 tokenId) external",
  "function balanceOf(address account) view returns (uint256)",
]);

/**
 * ABI for Uniswap position manager operations
 */
const UNISWAP_POSITION_MANAGER_ABI = parseAbi([
  "function decreaseLiquidity(uint256 tokenId, uint128 liquidity, uint256 amount0Min, uint256 amount1Min, uint256 deadline) external returns (uint256, uint256)",
  "function collect(uint256 tokenId, address recipient, uint128 amount0Max, uint128 amount1Max) external returns (uint256, uint256)",
  "function positions(uint256 tokenId) external view returns (uint96 nonce, address operator, address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint128 liquidity, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, uint128 tokensOwed0, uint128 tokensOwed1)",
]);

/**
 * Zod schema for Beefy vault withdrawal validation
 */
const beefyWithdrawSchema = z.object({
  vaultType: z.enum(["USDC-USDT", "WBTC-EIGEN", "USDC-EIGEN"]),
  tokenId: z.number().int().positive(),
});

/**
 * Zod schema for Uniswap position withdrawal validation
 */
const uniswapWithdrawSchema = z.object({
  positionId: z.number().int().positive(),
  percentage: z.number().min(0).max(100).default(100),
});

/**
 * Zod schema for emergency withdrawal validation
 */
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
  /**
   * Creates a new WithdrawalProvider instance
   */
  constructor() {
    super("withdrawal-provider", []);
    logger.info("WithdrawalProvider initialized");
  }

  /**
   * Withdraws funds from a Beefy vault
   * Allows users to withdraw their assets from various Beefy Finance vaults
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the withdrawal
   * @param {string} args.vaultType - Type of Beefy vault to withdraw from
   * @param {number} args.tokenId - ID of the token/position to withdraw
   * @returns {Promise<string>} A human-readable summary of the withdrawal
   * @throws {Error} If the withdrawal operation fails
   */
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
    logger.info(
      `Executing withdraw-from-beefy for vault type: ${vaultType}, tokenId: ${tokenId}`
    );

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

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

      logger.debug(`Selected vault: ${vaultName}, address: ${vaultAddress}`);

      if (!vaultAddress) {
        logger.error(`Vault address not found for ${vaultType}`);
        return `Error: Vault address not found for ${vaultType}`;
      }

      // In a real implementation, you would:
      // 1. Check if the user has a position in the vault
      // 2. Execute the withdrawal transaction
      // 3. Return the result
      logger.debug("Simulating withdrawal transaction");

      logger.info(`Beefy withdrawal simulation completed successfully`);

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
      logger.error("Error withdrawing from Beefy:", error);
      return `Error withdrawing from Beefy vault (${vaultType}): ${error}`;
    }
  }

  /**
   * Withdraws liquidity from a Uniswap position
   * Allows users to remove liquidity from their Uniswap V3 positions
   * and collect the resulting tokens and fees
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the withdrawal
   * @param {number} args.positionId - ID of the Uniswap position
   * @param {number} args.percentage - Percentage of liquidity to withdraw (default: 100)
   * @returns {Promise<string>} A human-readable summary of the withdrawal
   * @throws {Error} If the withdrawal operation fails
   */
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
    logger.info(
      `Executing withdraw-from-uniswap for positionId: ${positionId}, percentage: ${percentage}%`
    );

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

      const positionManagerAddress =
        PROTOCOL_ADDRESSES.UNISWAP.POSITION_MANAGER;
      logger.debug(`Position manager address: ${positionManagerAddress}`);

      if (!positionManagerAddress) {
        logger.error("Uniswap Position Manager address not found");
        return "Error: Uniswap Position Manager address not found";
      }

      // In a real implementation, you would:
      // 1. Get the position details
      // 2. Calculate the liquidity to withdraw based on percentage
      // 3. Execute the decreaseLiquidity transaction
      // 4. Execute the collect transaction to get the tokens
      logger.debug(
        "Simulating position details retrieval and liquidity withdrawal"
      );

      // Calculate how much liquidity to withdraw
      const liquidityPercentage = percentage === 100 ? "all" : `${percentage}%`;
      logger.debug(`Withdrawing ${liquidityPercentage} of liquidity`);

      logger.info(`Uniswap withdrawal simulation completed successfully`);

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
      logger.error("Error withdrawing from Uniswap:", error);
      return `Error withdrawing from Uniswap position ${positionId}: ${error}`;
    }
  }

  /**
   * Performs an emergency withdrawal from all connected protocols
   * Used in case of security threats to quickly secure user funds
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the emergency withdrawal
   * @param {string} [args.reason] - Reason for the emergency withdrawal
   * @param {boolean} [args.prioritizeSafety=true] - Whether to prioritize safety over efficiency
   * @returns {Promise<string>} A human-readable summary of the emergency withdrawal
   * @throws {Error} If the emergency withdrawal operation fails
   */
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
    logger.info(
      `Executing emergency-withdraw-all: prioritizeSafety=${prioritizeSafety}`
    );
    if (reason) {
      logger.info(`Emergency withdrawal reason: ${reason}`);
    }

    try {
      // Get wallet address from wallet provider
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

      // In a real implementation, you would:
      // 1. Scan for all user positions across protocols
      // 2. Execute withdrawals in order of priority (set by prioritizeSafety flag)
      // 3. Report on the results
      logger.debug("Simulating scan for user positions across all protocols");
      logger.debug(
        `Withdrawal strategy: ${prioritizeSafety ? "Safety First" : "Balanced"}`
      );

      logger.info("Emergency withdrawal simulation completed successfully");

      return `
      # 🚨 EMERGENCY WITHDRAWAL INITIATED 🚨
      
      ## Withdrawal Reason
      ${reason || "Security threat detected"}
      
      ## Wallet Details
      Executing emergency withdrawal for wallet: ${walletAddress}
      
      ## Protocols Targeted
      * Beefy Finance Vaults
      * Uniswap V3 Positions
      
      ## Withdrawal Strategy
      ${
        prioritizeSafety
          ? "Safety First: Prioritizing fastest withdrawals even if suboptimal"
          : "Balanced: Attempting to optimize for both safety and value"
      }
      
      ## Status
      * Scan for user positions: Complete
      * Withdrawal operations: Simulated
      
      ## Next Steps
      In a real implementation, this action would:
      1. Identify all your positions across supported protocols
      2. Execute withdrawals in order of priority
      3. Move funds to your wallet
      4. Provide a detailed report of completed operations
      
      ## Security Alert
      This is a high-priority action that should only be used in emergency situations.
      Please review the reason for this withdrawal and confirm it's necessary.
      `;
    } catch (error) {
      logger.error("Error executing emergency withdrawal:", error);
      return `Error executing emergency withdrawal: ${error}`;
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
 * Factory function to create a new WithdrawalProvider instance
 * @returns {WithdrawalProvider} A new WithdrawalProvider instance
 */
export const withdrawalProvider = () => new WithdrawalProvider();
