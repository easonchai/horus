# Token Handling in Horus

This document details the token detection and normalization system in Horus, which ensures consistent reference to tokens throughout the application and provides proper integration with blockchain operations.

## Overview

Tokens in DeFi can be referenced in various ways (e.g., "USDC", "usdc", "USD Coin"). To ensure consistency and accurate operation, Horus implements a robust token detection and normalization system that:

1. Dynamically loads token data from configuration
2. Detects token references in incoming signals
3. Normalizes token symbols to match configuration entries
4. Provides token metadata like addresses and decimals
5. Handles errors gracefully with appropriate fallbacks

## Token Configuration

Tokens are configured in `src/data/tokens.json`, which defines:

- Token names
- Standard symbols
- Decimal precision
- Network-specific contract addresses

Example token configuration:

```json
{
  "tokens": [
    {
      "name": "USD Coin",
      "symbol": "USDC",
      "decimals": 6,
      "networks": {
        "84532": "0xaE5554056c25bd179601bF64A296da0A3851a64d"
      }
    },
    {
      "name": "USD Tether",
      "symbol": "USDT",
      "decimals": 6,
      "networks": {
        "84532": "0xB4a65206bFBCA641332d080D1ac6283524A92783"
      }
    }
  ]
}
```

## TokenService

The `TokenService` serves as a central access point for token data, providing optimized access through caching for performance:

```typescript
export class TokenService {
  // Static cache for token lookups to improve performance
  private static tokenSymbolMap: Map<string, string> | null = null;
  private static tokenDataCache: Token[] | null = null;

  /**
   * Verifies that the tokens.json file is correctly loaded
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
}
```

## Token Detection Process

The token detection process follows these steps:

1. Load all token symbols from configuration
2. Convert both the token symbols and the input content to lowercase for case-insensitive matching
3. Find all tokens mentioned in the content
4. Normalize each detected token symbol to the official spelling in the configuration

### Implementation

The `TokenService.detectTokensInContent` method centrally handles token detection with robust error handling:

```typescript
public static detectTokensInContent(content: string): string[] {
  if (!content) return [];

  try {
    const contentLower = content.toLowerCase();
    const allTokensLower = this.getAllTokenSymbolsLowercase();

    // Find matches in the content
    const matchedTokens = allTokensLower.filter(symbol =>
      contentLower.includes(symbol)
    );

    // Normalize token symbols
    return matchedTokens.map(match => {
      const normalized = this.getNormalizedTokenSymbol(match);
      return normalized || match; // Fallback to detected token if normalization fails
    });
  } catch (error) {
    console.error(`[TokenService] Error detecting tokens: ${error}`);
    return []; // Return empty array on error
  }
}
```

## Performance Optimization

The TokenService implements several optimizations:

1. **Token Symbol Map Caching**: A static cache for token symbol normalization avoids recreating the map for each lookup
2. **Token Data Caching**: The token data is cached to avoid repeated parsing of the JSON file
3. **Error Recovery**: All methods include robust error handling with graceful fallbacks
4. **Validation**: Configuration is validated to avoid errors from malformed data

Example of the optimized caching implementation:

```typescript
// Static cache initialization
private static tokenSymbolMap: Map<string, string> | null = null;
private static tokenDataCache: Token[] | null = null;

// Optimized token symbol lookup with caching
private static getTokenSymbolMap(): Map<string, string> {
  if (this.tokenSymbolMap !== null) {
    return this.tokenSymbolMap;
  }

  try {
    this.tokenSymbolMap = new Map(
      this.getTokenData().map((t) => [t.symbol.toLowerCase(), t.symbol])
    );
    return this.tokenSymbolMap;
  } catch (error) {
    console.error(`[TokenService] Error creating token symbol map: ${error}`);
    return new Map(); // Return empty map on error
  }
}
```

## Error Handling

The token handling system includes multiple layers of error handling:

1. **Configuration Validation**: The `isConfigValid` method validates the token configuration
2. **Missing Token Configuration**: If `tokens.json` is missing or empty, warning logs are generated, and appropriate fallbacks are used
3. **Normalization Failure**: If a token symbol can't be normalized, the system logs a warning and falls back to the detected symbol
4. **Exception Handling**: All operations are wrapped in try-catch blocks to prevent crashes
5. **Defensive Coding**: Null checks and validation prevent issues with unexpected data
6. **Validation Before Actions**: The `ActionExecutor` validates tokens before attempting on-chain actions

## Integration with Services

The TokenService is integrated with key Horus services:

### AgentService

The `AgentService` uses TokenService for dynamic token detection in signals:

```typescript
private extractTokens(content: string): string[] {
  return TokenService.detectTokensInContent(content);
}
```

### SignalEvaluator

The `SignalEvaluator` uses TokenService for reliable token detection:

```typescript
private detectTokens(content: string): string[] {
  return TokenService.detectTokensInContent(content);
}
```

### ActionComposer

The `ActionComposer` validates the default safe token during initialization and normalizes token references before action creation:

```typescript
constructor(private dependencyGraph: DependencyGraph) {
  this.agentService = new AgentService();

  // Validate DEFAULT_SAFE_TOKEN at initialization time
  if (!TokenService.isValidToken(this.DEFAULT_SAFE_TOKEN)) {
    console.warn(`Default safe token "${this.DEFAULT_SAFE_TOKEN}" not found in configuration. Will use first available token as fallback.`);
    // Set to first available token or keep default as last resort
    this.validatedSafeToken = TokenService.getAllTokenSymbols()[0] || this.DEFAULT_SAFE_TOKEN;
  } else {
    // Use the normalized symbol to ensure consistent casing
    this.validatedSafeToken = TokenService.getNormalizedTokenSymbol(this.DEFAULT_SAFE_TOKEN) || this.DEFAULT_SAFE_TOKEN;
  }
}
```

### ActionExecutor

The `ActionExecutor` resolves token addresses from the blockchain and validates tokens:

```typescript
// Validate token exists in configuration
const normalizedToken = TokenService.getNormalizedTokenSymbol(action.token);
if (!normalizedToken) {
  console.warn(`Invalid token ${action.token} - skipping action`);
  results.push({
    action,
    status: "failed",
    error: `Invalid token: ${action.token}`,
    timestamp: Date.now(),
  });
  continue;
}

// Get token address from configuration
const tokenAddress = TokenService.getTokenAddress(
  normalizedToken,
  this.DEFAULT_CHAIN_ID
);
```

## Best Practices

When working with tokens in Horus:

1. **Configuration**:

   - Update `tokens.json` when adding new tokens
   - Use the official token symbol with correct casing
   - Include token addresses for all supported chains

2. **Token References**:

   - Always normalize token symbols using `TokenService.getNormalizedTokenSymbol()`
   - Validate token existence with `TokenService.isValidToken()`
   - Retrieve token metadata from TokenService rather than hardcoding

3. **Token Detection**:

   - Use `TokenService.detectTokensInContent()` for content analysis
   - Handle cases where tokens may not be detected
   - Consider context when determining if a token mention is relevant

4. **Error Handling**:
   - Include fallbacks for tokens that aren't in the configuration
   - Log warnings for token-related issues but don't crash the application
   - Consider using a default token (like USDC) when specific tokens can't be determined
