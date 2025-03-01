import {
  ActionProvider,
  CreateAction,
  Network,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { z } from "zod";
import { getLogger } from "../utils/logger";
import { baseSepolia } from "viem/chains";
import protocols from "../data/protocols.json";

// Initialize logger for this component
const logger = getLogger("BeefyWithdrawalProvider");

/**
 * Zod schema for Beefy vault withdrawal
 */
const beefyWithdrawSchema = z.object({
  // Contract identification
  contractAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/, {
    message: "Contract address must be a valid Ethereum address",
  }),

  // Token ID is required for Beefy withdrawals
  tokenId: z.number().int().positive(),

  // Optional parameters
  gasLimit: z.string().optional(),
  maxFeePerGas: z.string().optional(),
  maxPriorityFeePerGas: z.string().optional(),
});

/**
 * BeefyWithdrawalProvider - Provider for withdrawing from Beefy vaults
 */
class BeefyWithdrawalProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("beefy-withdrawal-provider", []);
    logger.info("BeefyWithdrawalProvider initialized");
  }

  /**
   * Validates if the contract address is a valid Beefy vault
   */
  private isValidBeefyVault(address: string): boolean {
    const beefyVaults = Object.values(
      protocols.protocols.find((p) => p.name === "Beefy")?.chains?.["84532"] ||
        {}
    );

    const isValid = beefyVaults.includes(address);
    if (!isValid) {
      logger.error(
        `Address ${address} is not a valid Beefy vault. Valid vaults: ${beefyVaults.join(
          ", "
        )}`
      );
    }
    return isValid;
  }

  @CreateAction({
    name: "withdraw",
    description: "Withdraw from a Beefy vault",
    schema: beefyWithdrawSchema,
  })
  async withdraw(
    walletProvider: WalletProvider,
    args: z.infer<typeof beefyWithdrawSchema>
  ): Promise<string> {
    const {
      contractAddress,
      tokenId,
      gasLimit,
      maxFeePerGas,
      maxPriorityFeePerGas,
    } = args;

    try {
      // Validate vault address
      if (!this.isValidBeefyVault(contractAddress)) {
        return `Error: ${contractAddress} is not a valid Beefy vault`;
      }

      // Get wallet address
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get Beefy vault ABI
      const beefyAbi = protocols.protocols.find((p) => p.name === "Beefy")?.abis
        ?.BeefyVault;

      if (!beefyAbi) {
        throw new Error("Beefy vault ABI not found");
      }

      // Initialize wallet
      const { Wallet } = await import("../wallet");
      const wallet = new Wallet();
      wallet.initialize();

      const publicClient = wallet.publicClient;
      const walletClient = wallet.walletClient;

      if (!walletClient || !publicClient) {
        throw new Error("Failed to get wallet client or public client");
      }

      // Get nonce
      const nonce = await publicClient.getTransactionCount({
        address: userAddress as `0x${string}`,
      });

      // Build transaction parameters
      const txParams = {
        address: contractAddress as `0x${string}`,
        abi: beefyAbi,
        functionName: "withdraw",
        args: [BigInt(tokenId)],
        chain: baseSepolia,
        nonce,
      } as any;

      // Execute transaction
      logger.info("Executing Beefy vault withdrawal");
      const hash = await walletClient.writeContract(txParams);
      logger.info(`Transaction submitted with hash: ${hash}`);

      // Wait for receipt
      const receipt = await publicClient.waitForTransactionReceipt({ hash });

      return `
      # Beefy Vault Withdrawal

      ## Transaction Details
      * Status: ${receipt.status === "success" ? "✅ Success" : "❌ Failed"}
      * Transaction Hash: ${hash}
      * Block Number: ${receipt.blockNumber}
      * Gas Used: ${receipt.gasUsed}

      ## Withdrawal Details
      * Vault Address: ${contractAddress}
      * Token ID: ${tokenId}
      * Wallet Address: ${userAddress}
      `;
    } catch (error) {
      logger.error("Error performing Beefy withdrawal:", error);
      return `Error withdrawing from Beefy vault: ${error}`;
    }
  }

  supportsNetwork = (network: Network) => {
    const chainId =
      typeof network.chainId === "string"
        ? parseInt(network.chainId, 10)
        : network.chainId;
    return chainId === 84532; // Base Sepolia
  };
}

export const beefyWithdrawalProvider = () => new BeefyWithdrawalProvider();
