import * as dotenv from "dotenv";
import { createWalletClient, http, WalletClient } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains";

// Load environment variables from .env file
dotenv.config();
/**
 * Service for managing wallet interactions
 * Uses Viem to connect to Base Sepolia testnet
 */
export class Wallet {
  private walletClient: WalletClient | null = null;

  constructor() {
    // Initialize wallet with private key from env
    const privateKey = process.env.PRIVATE_KEY || "";

    if (!privateKey) {
      console.warn("No private key found in environment variables");
      return;
    }

    try {
      // Format private key correctly (add 0x prefix if needed)
      const formattedKey = privateKey.startsWith("0x")
        ? (privateKey as `0x${string}`)
        : (`0x${privateKey}` as `0x${string}`);

      // Create account from private key
      const account = privateKeyToAccount(formattedKey);

      // Create wallet client
      this.walletClient = createWalletClient({
        account,
        chain: baseSepolia,
        transport: http("https://sepolia.base.org"),
      });

      console.log("Wallet initialized successfully");
    } catch (error) {
      console.error("Failed to initialize wallet:", error);
    }
  }

  /**
   * Get the wallet client instance
   * @returns The Viem wallet client or null if initialization failed
   */
  getWalletClient() {
    return this.walletClient;
  }
}
