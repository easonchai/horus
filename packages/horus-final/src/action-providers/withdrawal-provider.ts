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
import { getLogger } from "../utils/logger";

// Initialize logger for this component
const logger = getLogger("WithdrawalProvider");

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
    .array(z.any())
    .optional()
    .describe(
      "Contract ABI for the function being called (alternative to functionSignature)"
    ),

  // Function arguments
  args: z
    .array(z.any())
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
      protocol,
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

    logger.info(
      `Executing withdrawal for protocol: ${protocol}, contract: ${contractAddress}, function: ${functionName}`
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
      const walletAddress = await walletProvider.getAddress();
      logger.info(`User wallet address: ${walletAddress}`);

      // Process args and function name
      let processedArgs = [...functionArgs];
      let processedFunctionName = protocolAction || functionName;

      // Apply generic argument handling
      if (
        tokenId &&
        processedArgs.length === 0 &&
        processedFunctionName.toLowerCase().includes("withdraw")
      ) {
        logger.debug("Adding tokenId as the first argument for withdrawal");
        processedArgs = [tokenId];
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

      // Get the appropriate ABI
      let contractAbi;
      if (abi) {
        contractAbi = abi;
        logger.debug("Using provided ABI");
      } else if (functionSignature) {
        logger.debug(`Using function signature: ${functionSignature}`);
        contractAbi = parseAbi([functionSignature]);
      } else {
        logger.warn(
          "No ABI or function signature provided, attempting a minimal ABI for the function"
        );
        // Create a minimal ABI based on function name and args
        const argTypes = processedArgs
          .map((arg) => {
            if (
              typeof arg === "string" &&
              arg.startsWith("0x") &&
              arg.length === 42
            )
              return "address";
            if (
              typeof arg === "bigint" ||
              (typeof arg === "number" && Number.isInteger(arg))
            )
              return "uint256";
            if (typeof arg === "boolean") return "bool";
            return "bytes"; // Default to bytes for unknown types
          })
          .join(",");

        const minimalSignature = `function ${processedFunctionName}(${argTypes})`;
        logger.debug(
          `Generated minimal function signature: ${minimalSignature}`
        );

        try {
          contractAbi = parseAbi([minimalSignature]);
        } catch (error) {
          logger.error(
            "Failed to create minimal ABI, requiring explicit ABI or signature"
          );
          return "Error: Either ABI or function signature must be provided. Could not generate a minimal ABI.";
        }
      }

      // Build transaction parameters for Viem
      const txParams: any = {
        address: contractAddress as Address,
        abi: contractAbi,
        functionName: processedFunctionName,
        args: processedArgs,
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

      // In a real implementation with ViemWalletProvider:
      // 1. Get the wallet client from the wallet provider
      // const walletClient = await walletProvider.getWalletClient();
      // 2. Use the writeContract method to execute the transaction
      // const hash = await walletClient.writeContract(txParams);
      // 3. If confirmation is requested, wait for it
      // if (waitForConfirmation) {
      //   await walletClient.waitForTransactionReceipt({
      //     hash,
      //     confirmations
      //   });
      // }
      // 4. If a callback URL is provided, notify of completion
      // if (callbackUrl) {
      //   await fetch(callbackUrl, {
      //     method: 'POST',
      //     headers: { 'Content-Type': 'application/json' },
      //     body: JSON.stringify({
      //       status: 'success',
      //       txHash: hash,
      //       metadata
      //     })
      //   });
      // }

      logger.debug(
        `Simulating Viem contract write call to ${processedFunctionName}`
      );

      if (waitForConfirmation) {
        logger.debug(`Will wait for ${confirmations} confirmation(s)`);
      }

      if (callbackUrl) {
        logger.debug(`Will notify ${callbackUrl} upon completion`);
      }

      logger.info(`Withdrawal simulation completed successfully`);

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

      // Return a formatted response
      const responseTitle = `${protocol} Withdrawal`;

      // Return a formatted mock response with Viem-specific details
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
      
      ## Transaction Details
      * Contract Address: ${contractAddress}
      * Function: ${processedFunctionName}
      * Wallet Address: ${walletAddress}
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
      * Status: Simulated
      
      ## Function Details
      * ${functionSignature || "Using provided or generated ABI"}
      * Arguments: ${JSON.stringify(
        processedArgs.map((arg) =>
          typeof arg === "bigint" ? arg.toString() : arg
        )
      )}
      
      ## Process
      In a real implementation, this would:
      1. Connect to the contract at ${contractAddress} using Viem wallet provider
      2. Call writeContract with the ${processedFunctionName} function and provided arguments
      3. ${
        waitForConfirmation
          ? `Wait for ${confirmations} confirmation(s) on the blockchain`
          : "Return the transaction hash immediately without waiting for confirmation"
      }
      4. ${
        callbackUrl
          ? `Notify the callback URL (${callbackUrl}) upon completion`
          : "Return the transaction receipt with details of the operation"
      }
      
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
