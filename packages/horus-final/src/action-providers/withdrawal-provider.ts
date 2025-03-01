/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  ActionProvider,
  CreateAction,
  Network,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { parseAbi } from "viem";
import { z } from "zod";
import { getLogger } from "../utils/logger";
import { baseSepolia } from "viem/chains";
import protocols from "../data/protocols.json";

// Initialize logger for this component
const logger = getLogger("WithdrawalProvider");

const MAX_UINT128 = BigInt("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"); // 2^128 - 1

/**
 * Zod schema for universal contract withdrawal validation
 * A flexible interface for withdrawing from any contract
 */
const universalWithdrawSchema = z.object({
  // Contract identification
  contractAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/, {
    message: "Contract address must be a valid Ethereum address",
  }),

  // Protocol information
  protocol: z
    .string()
    .describe(
      "Protocol name or identifier (e.g., 'uniswap', 'aave', 'custom')"
    ),

  protocolAction: z
    .string()
    .optional()
    .describe(
      "Specific protocol action (e.g., 'withdraw', 'decreaseLiquidity', 'exit')"
    ),

  // Protocol-specific parameters (flexible record to handle any protocol)
  protocolParams: z
    .record(z.string(), z.any())
    .optional()
    .describe("Protocol-specific parameters as key-value pairs"),

  // Chain information
  chainId: z
    .union([z.number(), z.string()])
    .default(84532)
    .describe("Chain ID for the withdrawal"),

  // Function details
  functionName: z.string().min(1, {
    message: "Function name is required",
  }),
  functionSignature: z
    .string()
    .optional()
    .describe(
      "Optional function signature if ABI is not provided (e.g., 'withdraw(uint256)')"
    ),
  abi: z
    .array(
      z.object({
        name: z.string().optional(),
        type: z.string().optional(),
        inputs: z
          .array(
            z.object({
              name: z.string().optional(),
              type: z.string(),
              indexed: z.boolean().optional(),
              components: z
                .array(
                  z.object({
                    name: z.string().optional(),
                    type: z.string(),
                  })
                )
                .optional(),
            })
          )
          .optional(),
        outputs: z
          .array(
            z.object({
              name: z.string().optional(),
              type: z.string(),
              components: z
                .array(
                  z.object({
                    name: z.string().optional(),
                    type: z.string(),
                  })
                )
                .optional(),
            })
          )
          .optional(),
        stateMutability: z.string().optional(),
        anonymous: z.boolean().optional(),
        constant: z.boolean().optional(),
      })
    )
    .optional()
    .describe(
      "Contract ABI for the function being called (alternative to functionSignature)"
    ),

  // Function arguments - Simplified schema to avoid nested array issues
  args: z
    .array(
      z.union([
        z.string(),
        z.number(),
        z.boolean(),
        z.bigint(),
        z.null(),
        // Remove nested array type and complex objects
        // Just handle primitive types that are commonly used in contract calls
        z.object({}).passthrough(), // Allow any object structure
      ])
    )
    .default([])
    .describe("Arguments to pass to the contract function"),

  // Asset identifiers
  tokenId: z
    .number()
    .int()
    .positive()
    .optional()
    .describe("Token ID for NFT-based withdrawals (e.g., LP positions)"),
  percentage: z
    .number()
    .min(0)
    .max(100)
    .default(100)
    .describe("Percentage of assets to withdraw (0-100)"),

  // Asset information
  assetName: z
    .string()
    .optional()
    .describe("Name of the asset being withdrawn (for better reporting)"),
  assetSymbol: z
    .string()
    .optional()
    .describe("Symbol of the asset being withdrawn"),
  assetDecimals: z
    .number()
    .int()
    .min(0)
    .max(18)
    .optional()
    .describe("Decimals of the asset being withdrawn"),
  assetAddress: z
    .string()
    .regex(/^0x[a-fA-F0-9]{40}$/, {
      message: "Asset address must be a valid Ethereum address",
    })
    .optional()
    .describe("Asset contract address"),

  // Transaction parameters
  value: z
    .string()
    .optional()
    .describe(
      "Amount of native currency to send with the transaction (in wei)"
    ),
  gasLimit: z
    .string()
    .optional()
    .describe("Optional gas limit for the transaction"),
  maxFeePerGas: z
    .string()
    .optional()
    .describe("Maximum fee per gas (in wei) for EIP-1559 transactions"),
  maxPriorityFeePerGas: z
    .string()
    .optional()
    .describe(
      "Maximum priority fee per gas (in wei) for EIP-1559 transactions"
    ),

  // Transaction handling
  waitForConfirmation: z
    .boolean()
    .default(true)
    .describe("Whether to wait for transaction confirmation"),
  confirmations: z
    .number()
    .int()
    .min(1)
    .default(1)
    .describe("Number of confirmations to wait for"),

  // Emergency parameters
  prioritizeSafety: z
    .boolean()
    .default(true)
    .describe(
      "For emergency withdrawals: prioritize safety over optimal returns"
    ),
  reason: z.string().optional().describe("Reason for emergency withdrawal"),

  // General
  description: z
    .string()
    .optional()
    .describe("Human-readable description of what this withdrawal is doing"),

  // Callback parameters
  callbackUrl: z
    .string()
    .url()
    .optional()
    .describe("URL to call when the withdrawal is complete"),

  // Additional arbitrary data (useful for AI systems to pass context)
  metadata: z
    .record(z.string(), z.any())
    .optional()
    .describe("Additional metadata or context about the withdrawal operation"),
});

/**
 * Helper function to get the correct ABI based on protocol and function
 */
const getProtocolABI = (protocolName: string, contractType: string) => {
  const protocol = protocols.protocols.find((p) => p.name === protocolName);
  if (!protocol) {
    throw new Error(`Protocol ${protocolName} not found in configuration`);
  }

  const abi = (protocol as any).abis?.[contractType] as any;
  if (!abi) {
    throw new Error(
      `ABI for ${contractType} not found in ${protocolName} configuration`
    );
  }

  return abi;
};

/**
 * Helper function to validate if an address belongs to a protocol
 */
const isValidProtocolContract = (
  protocol: string,
  address: string
): boolean => {
  const protocolData = protocols.protocols.find(
    (p) => p.name.toLowerCase() === protocol.toLowerCase()
  );

  if (!protocolData?.chains?.["84532"]) {
    logger.error(`No contracts found for protocol ${protocol} on chain 84532`);
    return false;
  }

  const validAddresses = Object.values(protocolData.chains["84532"]);
  const isValid = validAddresses.includes(address);

  if (!isValid) {
    logger.error(
      `Address ${address} is not a valid contract for protocol ${protocol}. Valid addresses: ${validAddresses.join(
        ", "
      )}`
    );
  }

  return isValid;
};

/**
 * Helper function to normalize protocol name
 */
const normalizeProtocolName = (protocol: string): string => {
  if (protocol.toLowerCase() === "uniswap") return "UniswapV3";
  if (protocol.toLowerCase() === "beefy") return "Beefy";
  return protocol;
};

/**
 * WithdrawalProvider - A generic action provider for withdrawing assets from any contract
 *
 * This provider allows users to withdraw their funds from any contract without
 * any hardcoded protocol knowledge. All necessary information must be provided in the request.
 */
export class WithdrawalProvider extends ActionProvider<WalletProvider> {
  /**
   * Creates a new WithdrawalProvider instance
   */
  constructor() {
    super("withdrawal-provider", []);
    logger.info("Generic WithdrawalProvider initialized");
  }

  /**
   * Universal withdrawal method for any contract
   * Provides a flexible interface for interacting with any withdrawal function
   * Optimized for Viem wallet interactions
   *
   * @param {WalletProvider} walletProvider - Provider for wallet interactions
   * @param {object} args - Arguments for the withdrawal
   * @returns {Promise<string>} A human-readable summary of the withdrawal
   * @throws {Error} If the withdrawal operation fails
   */
  @CreateAction({
    name: "withdraw",
    description: "Universal withdrawal function for any contract",
    schema: universalWithdrawSchema,
  })
  async withdraw(
    walletProvider: WalletProvider,
    args: z.infer<typeof universalWithdrawSchema>
  ): Promise<string> {
    const {
      contractAddress,
      protocol: rawProtocol,
      protocolAction,
      protocolParams,
      chainId,
      functionName,
      functionSignature,
      abi,
      args: functionArgs,
      tokenId,
      percentage,
      assetName,
      assetSymbol,
      assetDecimals,
      assetAddress,
      value,
      gasLimit,
      maxFeePerGas,
      maxPriorityFeePerGas,
      waitForConfirmation,
      confirmations,
      prioritizeSafety,
      reason,
      description,
      callbackUrl,
      metadata,
    } = args;

    // Normalize protocol name
    const protocol = normalizeProtocolName(rawProtocol);

    // Validate contract address belongs to protocol
    if (!isValidProtocolContract(protocol, contractAddress)) {
      return `Error: Contract address ${contractAddress} is not a valid contract for protocol ${protocol}`;
    }

    logger.info(
      `Executing withdrawal for protocol: ${protocol}, contract: ${contractAddress}, function: ${
        protocolAction || functionName
      }`
    );

    // Log protocol-specific parameters if provided
    if (protocolParams) {
      logger.info(`Protocol params: ${JSON.stringify(protocolParams)}`);
    }

    // Log additional metadata if provided
    if (metadata) {
      logger.info(`Additional metadata: ${JSON.stringify(metadata)}`);
    }

    // Log asset details if provided
    if (assetName || assetSymbol || assetAddress) {
      logger.info(
        `Asset details: ${assetName || ""} ${
          assetSymbol ? `(${assetSymbol})` : ""
        } ${assetAddress ? `at ${assetAddress}` : ""}`
      );
    }

    try {
      // Get wallet address from wallet provider
      const userAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${userAddress}`);

      // Process args and function name
      let processedArgs = [...functionArgs];
      let processedFunctionName = protocolAction || functionName;

      // Special handling for Uniswap V3 NonfungiblePositionManager functions
      if (protocol === "UniswapV3") {
        // Validate contract is NonfungiblePositionManager
        const nftManager = protocols.protocols.find(
          (p) => p.name === "UniswapV3"
        )?.chains?.["84532"]?.nonfungiblePositionManager;

        if (contractAddress !== nftManager) {
          throw new Error(
            `Invalid contract address for UniswapV3 NonfungiblePositionManager. Expected ${nftManager}, got ${contractAddress}`
          );
        }

        logger.info(
          `Validated UniswapV3 NFT Manager contract: ${contractAddress}`
        );

        if (protocolAction === "decreaseLiquidity") {
          logger.info("Processing decreaseLiquidity params for UniswapV3");
          processedArgs = [
            {
              tokenId: BigInt(tokenId || 0),
              liquidity: BigInt(protocolParams?.liquidity || 0),
              amount0Min: BigInt(protocolParams?.amount0Min || 0),
              amount1Min: BigInt(protocolParams?.amount1Min || 0),
              deadline: BigInt(
                protocolParams?.deadline || Math.floor(Date.now() / 1000) + 1800
              ),
            },
          ];
          logger.debug(
            `decreaseLiquidity params: ${JSON.stringify(processedArgs)}`
          );
        } else if (protocolAction === "collect") {
          logger.info("Processing collect params for UniswapV3");
          processedArgs = [
            {
              tokenId: BigInt(tokenId || 0),
              recipient: userAddress as `0x${string}`,
              amount0Max: BigInt(protocolParams?.amount0Max || MAX_UINT128),
              amount1Max: BigInt(protocolParams?.amount1Max || MAX_UINT128),
            },
          ];
          logger.debug(`collect params: ${JSON.stringify(processedArgs)}`);
        }
      } else if (protocol === "Beefy" && protocolAction === "withdraw") {
        // Validate contract is a Beefy vault
        const beefyVaults = Object.values(
          protocols.protocols.find((p) => p.name === "Beefy")?.chains?.[
            "84532"
          ] || {}
        );

        if (!beefyVaults.includes(contractAddress)) {
          throw new Error(
            `Invalid contract address for Beefy vault. Valid vaults: ${beefyVaults.join(
              ", "
            )}`
          );
        }

        logger.info(`Validated Beefy vault contract: ${contractAddress}`);

        // Simple tokenId argument for Beefy
        processedArgs = [BigInt(tokenId || 0)];
        logger.debug(`Beefy withdraw params: tokenId=${tokenId}`);
      }

      // Process any numbers in protocol params
      if (protocolParams) {
        logger.debug(`Processing protocol params for ${protocol}`);

        // Convert any string numbers to BigInt if they look like they need conversion
        for (const [key, value] of Object.entries(protocolParams)) {
          if (
            typeof value === "string" &&
            /^\d+$/.test(value) &&
            (key.toLowerCase().includes("amount") ||
              key.toLowerCase().includes("value") ||
              key.toLowerCase().includes("wei") ||
              key.toLowerCase().includes("min") ||
              key.toLowerCase().includes("max"))
          ) {
            logger.debug(
              `Converting string value for ${key} to BigInt: ${value}`
            );
            protocolParams[key] = BigInt(value);
          }
        }
      }

      // Determine the correct ABI to use
      let contractAbi;
      if (abi) {
        contractAbi = abi;
        logger.debug("Using provided ABI");
      } else if (protocol === "UniswapV3") {
        if (
          protocolAction === "decreaseLiquidity" ||
          protocolAction === "collect"
        ) {
          contractAbi = getProtocolABI(
            "UniswapV3",
            "NonfungiblePositionManager"
          );
          logger.info("Using UniswapV3 NonfungiblePositionManager ABI");
        }
      } else if (protocol === "Beefy") {
        if (protocolAction === "withdraw") {
          contractAbi = getProtocolABI("Beefy", "BeefyVault");
          logger.info("Using Beefy vault ABI");
        }
      } else if (functionSignature) {
        logger.debug(`Using function signature: ${functionSignature}`);
        contractAbi = parseAbi([functionSignature]);
      } else {
        throw new Error(
          "No ABI, protocol-specific ABI, or function signature provided"
        );
      }

      // Log the final contract call details
      logger.info(`
        Final contract call details:
        Protocol: ${protocol}
        Contract: ${contractAddress}
        Function: ${processedFunctionName}
        Args: ${JSON.stringify(processedArgs, (_, v) =>
          typeof v === "bigint" ? v.toString() : v
        )}
      `);

      // Build transaction parameters for Viem
      const txParams: any = {
        address: contractAddress as `0x${string}`,
        abi: contractAbi,
        functionName: processedFunctionName,
        args: processedArgs,
        chain: baseSepolia,
      };

      // Add optional transaction parameters if provided
      if (value) {
        txParams.value = BigInt(value);
        logger.debug(`Transaction value: ${value} wei`);
      }

      if (gasLimit) {
        txParams.gas = BigInt(gasLimit);
        logger.debug(`Gas limit: ${gasLimit}`);
      }

      // Add EIP-1559 fee parameters if provided
      if (maxFeePerGas) {
        txParams.maxFeePerGas = BigInt(maxFeePerGas);
        logger.debug(`Max fee per gas: ${maxFeePerGas} wei`);
      }

      if (maxPriorityFeePerGas) {
        txParams.maxPriorityFeePerGas = BigInt(maxPriorityFeePerGas);
        logger.debug(`Max priority fee per gas: ${maxPriorityFeePerGas} wei`);
      }

      // Log the transaction parameters
      logger.debug(
        `Transaction parameters: ${JSON.stringify({
          ...txParams,
          // Convert BigInts to strings for logging
          value: value ? value : undefined,
          gas: gasLimit ? gasLimit : undefined,
          maxFeePerGas: maxFeePerGas ? maxFeePerGas : undefined,
          maxPriorityFeePerGas: maxPriorityFeePerGas
            ? maxPriorityFeePerGas
            : undefined,
          args: processedArgs.map((arg) =>
            typeof arg === "bigint" ? arg.toString() : arg
          ),
        })}`
      );

      // REAL IMPLEMENTATION WITH VIEM
      logger.info("Creating Wallet instance from wallet utility");
      const { Wallet } = await import("../wallet");
      const wallet = new Wallet();

      // Make sure wallet is initialized
      wallet.initialize();

      const publicClient = wallet.publicClient;
      const walletClient = wallet.walletClient;

      if (!walletClient || !publicClient) {
        throw new Error("Failed to get wallet client or public client");
      }

      // Get the transaction count for nonce
      const transactionCount = await publicClient.getTransactionCount({
        address: userAddress as `0x${string}`,
      });

      // Add chain and nonce to transaction parameters
      txParams.nonce = transactionCount;

      logger.info("Executing contract write call");
      const hash = await walletClient.writeContract(txParams as any);
      logger.info(`Transaction submitted with hash: ${hash}`);

      let receipt = null;
      // If confirmation is requested, wait for it
      if (waitForConfirmation) {
        logger.info(`Waiting for ${confirmations || 1} confirmation(s)...`);
        receipt = await publicClient.waitForTransactionReceipt({
          hash,
          confirmations: confirmations || 1,
        });
        logger.info(`Transaction confirmed in block ${receipt.blockNumber}`);

        if (receipt.status !== "success") {
          throw new Error("Transaction failed");
        }
      }

      // If a callback URL is provided, notify of completion
      if (callbackUrl) {
        logger.info(`Notifying callback URL: ${callbackUrl}`);
        try {
          await fetch(callbackUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              status: "success",
              txHash: hash,
              receipt: receipt
                ? {
                    blockNumber: receipt.blockNumber,
                    gasUsed: receipt.gasUsed.toString(),
                    effectiveGasPrice: receipt.effectiveGasPrice.toString(),
                    status: receipt.status,
                  }
                : null,
              metadata,
            }),
          });
          logger.info("Callback notification sent successfully");
        } catch (callbackError) {
          logger.error(`Failed to notify callback URL: ${callbackError}`);
        }
      }

      // Format protocol parameters for display
      const protocolParamsFormatted = protocolParams
        ? Object.entries(protocolParams)
            .map(([key, value]) => {
              const valueStr =
                typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value);
              return `* ${key}: ${valueStr}`;
            })
            .join("\n          ")
        : "* None provided";

      // Format any metadata for display
      const metadataFormatted = metadata
        ? Object.entries(metadata)
            .map(([key, value]) => {
              const valueStr =
                typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value);
              return `* ${key}: ${valueStr}`;
            })
            .join("\n          ")
        : "";

      // Add asset information if available
      let assetDetails = "";
      if (assetName || assetSymbol || assetAddress) {
        assetDetails = `
        ## Asset Information
        ${assetName ? `* Name: ${assetName}` : ""}
        ${assetSymbol ? `* Symbol: ${assetSymbol}` : ""}
        ${assetDecimals ? `* Decimals: ${assetDecimals}` : ""}
        ${assetAddress ? `* Address: ${assetAddress}` : ""}`;
      }

      // Add transaction details
      const txDetails = `
      ## Transaction Details
      * Transaction Hash: ${hash}
      ${receipt ? `* Block Number: ${receipt.blockNumber}` : ""}
      ${receipt ? `* Gas Used: ${receipt.gasUsed.toString()}` : ""}
      ${
        receipt
          ? `* Status: ${receipt.status === "success" ? "Success" : "Failed"}`
          : "* Status: Pending"
      }`;

      // Return a formatted response
      const responseTitle = `${protocol} Withdrawal`;

      // Return a formatted response with REAL transaction details
      return `
      # ${responseTitle}
      
      ## Protocol Information
      * Protocol: ${protocol}
      * Chain ID: ${chainId}
      ${description ? `* Description: ${description}` : ""}
      ${reason ? `* Reason: ${reason}` : ""}
      
      ## Protocol Parameters
      ${protocolParamsFormatted}
      ${assetDetails}
      ${
        metadataFormatted
          ? `\n      ## Additional Metadata\n      ${metadataFormatted}`
          : ""
      }
      ${txDetails}
      
      ## Contract Details
      * Contract Address: ${contractAddress}
      * Function: ${processedFunctionName}
      * Wallet Address: ${userAddress}
      ${tokenId ? `* Token ID: ${tokenId}` : ""}
      ${percentage !== 100 ? `* Withdrawal Percentage: ${percentage}%` : ""}
      ${value ? `* Value Sent: ${value} wei` : ""}
      ${gasLimit ? `* Gas Limit: ${gasLimit}` : ""}
      ${maxFeePerGas ? `* Max Fee Per Gas: ${maxFeePerGas} wei` : ""}
      ${
        maxPriorityFeePerGas
          ? `* Max Priority Fee Per Gas: ${maxPriorityFeePerGas} wei`
          : ""
      }
      * Wait For Confirmation: ${waitForConfirmation ? "Yes" : "No"}
      ${waitForConfirmation ? `* Confirmations Required: ${confirmations}` : ""}
      ${callbackUrl ? `* Callback URL: ${callbackUrl}` : ""}
      
      ## Function Details
      * ${functionSignature || "Using provided or generated ABI"}
      * Arguments: ${JSON.stringify(
        processedArgs.map((arg) =>
          typeof arg === "bigint" ? arg.toString() : arg
        )
      )}
      
      ## Next Steps
      * You can view this transaction on a block explorer
      * The withdrawal should be completed ${
        receipt ? "successfully" : "once confirmed"
      }
      * Always verify that your funds have been received after a withdrawal
      
      ## Security Considerations
      * Always verify contract addresses before interacting with them
      * Ensure you understand the function you're calling and its potential effects
      * Consider setting appropriate gas parameters during network congestion
      * For high-value transactions, consider using a hardware wallet with the provider
      `;
    } catch (error) {
      logger.error("Error performing withdrawal:", error);
      return `Error performing withdrawal from ${contractAddress}: ${error}`;
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
