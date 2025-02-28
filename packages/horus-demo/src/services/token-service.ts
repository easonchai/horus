import tokensData from "../data/tokens.json";
import { Token } from "../models/types";

/**
 * Service for managing token data and normalization
 * Provides centralized access to token information from tokens.json
 */
export class TokenService {
  // Static cache for token lookups to improve performance
  private static tokenSymbolMap: Map<string, string> | null = null;
  private static tokenDataCache: Token[] | null = null;

  /**
   * Verifies that the tokens.json file is correctly loaded
   * @returns true if tokens data exists and has tokens array
   */
  private static isConfigValid(): boolean {
    return (
      tokensData !== undefined &&
      tokensData !== null &&
      Array.isArray(tokensData.tokens)
    );
  }

  /**
   * Returns token data from the JSON with validation
   */
  public static getTokenData(): Token[] {
    if (this.tokenDataCache !== null) {
      return this.tokenDataCache;
    }

    if (!this.isConfigValid()) {
      console.warn(
        "[TokenService] Invalid or missing tokens.json configuration"
      );
      this.tokenDataCache = [];
      return [];
    }

    this.tokenDataCache = tokensData.tokens;
    return this.tokenDataCache;
  }

  /**
   * Returns all token symbols from the configuration
   */
  public static getAllTokenSymbols(): string[] {
    return this.getTokenData().map((t) => t.symbol);
  }

  /**
   * Returns all token symbols in lowercase for case-insensitive matching
   */
  public static getAllTokenSymbolsLowercase(): string[] {
    return this.getAllTokenSymbols().map((symbol) => symbol.toLowerCase());
  }

  /**
   * Creates and returns a case-insensitive token symbol lookup map
   * Uses a cached version if available for better performance
   */
  private static getTokenSymbolMap(): Map<string, string> {
    if (this.tokenSymbolMap !== null) {
      return this.tokenSymbolMap;
    }

    try {
      // Create mapping for case-insensitive lookups
      this.tokenSymbolMap = new Map(
        this.getTokenData().map((t) => [t.symbol.toLowerCase(), t.symbol])
      );
      return this.tokenSymbolMap;
    } catch (error) {
      console.error(`[TokenService] Error creating token symbol map: ${error}`);
      return new Map(); // Return empty map on error
    }
  }

  /**
   * Normalizes token symbols to match exact case in tokens.json
   * Uses cached symbol map for better performance
   */
  public static getNormalizedTokenSymbol(symbol: string): string | undefined {
    if (!symbol) return undefined;

    try {
      const symbolMap = this.getTokenSymbolMap();
      return symbolMap.get(symbol.toLowerCase());
    } catch (error) {
      console.error(`[TokenService] Error normalizing token symbol: ${error}`);
      return undefined;
    }
  }

  /**
   * Gets token details by symbol
   */
  public static getTokenBySymbol(symbol: string): Token | undefined {
    if (!symbol) return undefined;

    try {
      const normalizedSymbol = this.getNormalizedTokenSymbol(symbol);

      if (!normalizedSymbol) return undefined;

      return this.getTokenData().find((t) => t.symbol === normalizedSymbol);
    } catch (error) {
      console.error(`[TokenService] Error getting token by symbol: ${error}`);
      return undefined;
    }
  }

  /**
   * Gets token address for a specific chain
   */
  public static getTokenAddress(
    symbol: string,
    chainId: string
  ): string | undefined {
    if (!symbol || !chainId) return undefined;

    try {
      const token = this.getTokenBySymbol(symbol);

      if (!token || !token.networks) return undefined;

      return token.networks[chainId];
    } catch (error) {
      console.error(`[TokenService] Error getting token address: ${error}`);
      return undefined;
    }
  }

  /**
   * Checks if a token exists in the configuration
   */
  public static isValidToken(symbol: string): boolean {
    return Boolean(this.getNormalizedTokenSymbol(symbol));
  }

  /**
   * Detects token symbols mentioned in content
   */
  public static detectTokensInContent(content: string): string[] {
    if (!content) return [];

    try {
      const contentLower = content.toLowerCase();
      const allTokensLower = this.getAllTokenSymbolsLowercase();

      // Find matches in the content
      const matchedTokens = allTokensLower.filter((symbol) =>
        contentLower.includes(symbol)
      );

      // Normalize token symbols
      return matchedTokens.map((match) => {
        const normalized = this.getNormalizedTokenSymbol(match);
        return normalized || match;
      });
    } catch (error) {
      console.error(`[TokenService] Error detecting tokens: ${error}`);
      return [];
    }
  }

  /**
   * Clears the token cache (useful for testing)
   */
  public static clearCache(): void {
    this.tokenSymbolMap = null;
    this.tokenDataCache = null;
  }
}
