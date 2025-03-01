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
const logger = getLogger("UniswapWithdrawalProvider");

const MAX_UINT128 = BigInt("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"); // 2^128 - 1

/**
 * Zod schema for Uniswap position withdrawal
 */
const uniswapWithdrawSchema = z.object({
  contractAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
  action: z.enum(["decreaseLiquidity", "collect"]),
  tokenId: z.number().int().positive(),

  // decreaseLiquidity params
  liquidity: z.string(),
  amount0Min: z.string(),
  amount1Min: z.string(),
  deadline: z.number().describe("Current timestamp plus 5 minutes"),

  // // collect params
  // amount0Max: z.string(),
  // amount1Max: z.string(),
});

class UniswapWithdrawalProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("uniswap-withdrawal-provider", []);
    logger.info("UniswapWithdrawalProvider initialized");
  }

  private isValidNFTManager(address: string): boolean {
    const nftManager = protocols.protocols.find((p) => p.name === "UniswapV3")
      ?.chains?.["84532"]?.nonfungiblePositionManager;

    const isValid = address === nftManager;
    if (!isValid) {
      logger.error(
        `Invalid NFT manager address. Expected ${nftManager}, got ${address}`
      );
    }
    return isValid;
  }

  @CreateAction({
    name: "withdraw",
    description: "Withdraw from Uniswap V3 position",
    schema: uniswapWithdrawSchema,
  })
  async withdraw(
    walletProvider: WalletProvider,
    args: z.infer<typeof uniswapWithdrawSchema>
  ): Promise<string> {
    const {
      contractAddress,
      action,
      tokenId,
      liquidity,
      amount0Min,
      amount1Min,
    } = args;

    try {
      // Validate NFT manager address
      if (!this.isValidNFTManager(contractAddress)) {
        return `Error: ${contractAddress} is not the valid Uniswap V3 NFT manager`;
      }

      // Get wallet address
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Get NFT manager ABI
      const nftManagerAbi = protocols.protocols.find(
        (p) => p.name === "UniswapV3"
      )?.abis?.NonfungiblePositionManager;

      if (!nftManagerAbi) {
        throw new Error("Uniswap NFT manager ABI not found");
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

      // Prepare arguments based on action
      const processedArgs =
        action === "decreaseLiquidity"
          ? [
              BigInt(tokenId),
              BigInt(liquidity || 0),
              BigInt(amount0Min || 0),
              BigInt(amount1Min || 0),
              BigInt(Math.floor(Date.now() / 1000) + 1800),
            ]
          : [
              BigInt(tokenId),
              userAddress as `0x${string}`,
              // BigInt(amount0Max || MAX_UINT128),
              // BigInt(amount1Max || MAX_UINT128),
            ];

      logger.info(`
        Action: ${action}
        TokenId: ${tokenId}
        Args structure: ${JSON.stringify(processedArgs, (_, v) =>
          typeof v === "bigint" ? v.toString() : v
        )}
      `);

      // Build transaction parameters
      const txParams = {
        address: contractAddress as `0x${string}`,
        abi: nftManagerAbi,
        functionName: action,
        args: processedArgs,
        chain: baseSepolia,
        nonce,
      } as any;

      logger.info(`
        Transaction params:
        Address: ${txParams.address}
        Function: ${txParams.functionName}
        Args: ${JSON.stringify(txParams.args, (_, v) =>
          typeof v === "bigint" ? v.toString() : v
        )}
      `);

      // Execute transaction
      logger.info(`Executing Uniswap ${action}`);
      const hash = await walletClient.writeContract(txParams);
      logger.info(`Transaction submitted with hash: ${hash}`);

      // Wait for receipt
      const receipt = await publicClient.waitForTransactionReceipt({ hash });

      return `
      # Uniswap V3 Position ${action}

      ## Transaction Details
      * Status: ${receipt.status === "success" ? "✅ Success" : "❌ Failed"}
      * Transaction Hash: ${hash}
      * Block Number: ${receipt.blockNumber}
      * Gas Used: ${receipt.gasUsed}

      ## Position Details
      * NFT Manager: ${contractAddress}
      * Token ID: ${tokenId}
      * Action: ${action}
      * Wallet Address: ${userAddress}
      `;
    } catch (error) {
      logger.error(`Error performing Uniswap ${action}:`, error);
      return `Error with Uniswap position: ${error}`;
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

export const uniswapWithdrawalProvider = () => new UniswapWithdrawalProvider();
