import * as dotenv from "dotenv";
import {
  createWalletClient,
  createPublicClient,
  http,
  WalletClient,
  PublicClient,
} from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains";

// Load environment variables from .env file
dotenv.config();
/**
 * Service for managing wallet interactions
 * Uses Viem to connect to Base Sepolia testnet
 */
export class Wallet {
  public walletClient: WalletClient | null = null;
  public publicClient: any | null = null;

  constructor() {
    this.initialize();
  }

  /**
   * Initialize the wallet with private key
   */
  initialize() {
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

      // Create public client
      this.publicClient = createPublicClient({
        chain: baseSepolia,
        transport: http("https://sepolia.base.org"),
      });

      console.log("Wallet initialized successfully");
    } catch (error) {
      console.error("Failed to initialize wallet:", error);
    }
  }

  getAddress() {
    if (!this.walletClient) {
      throw new Error("Wallet client not initialized");
    }

    return this.walletClient.getAddresses();
  }

  /**
   * Get the wallet client instance
   * @returns The Viem wallet client or null if initialization failed
   */
  getWalletClient() {
    return this.walletClient;
  }

  /**
   * Get the public client instance
   * @returns The Viem public client or null if initialization failed
   */
  getPublicClient() {
    return this.publicClient;
  }

  /**
   * Get the chain instance
   * @returns The Viem chain instance or null if initialization failed
   */
  getChain() {
    return baseSepolia;
  }
}

// Create singleton instance
const walletInstance = new Wallet();

// Export functions to get clients
export const getWalletClient = () => walletInstance.walletClient;
export const getPublicClient = () => walletInstance.publicClient;
export const getChain = () => baseSepolia;
