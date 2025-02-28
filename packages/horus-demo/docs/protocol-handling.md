# Protocol Handling in Horus

This document details the protocol detection and normalization system in Horus, which is critical for ensuring that threats are accurately identified and properly mapped to the dependency graph.

## Overview

Protocols in DeFi often have multiple ways they might be referenced (e.g., "Uniswap", "uniswap", "UniswapV3"). To ensure consistency, Horus implements a robust protocol detection and normalization system that:

1. Dynamically loads protocol names from configuration
2. Detects mentions of protocols in incoming signals
3. Normalizes detected protocols to match configuration entries
4. Handles errors gracefully with appropriate fallbacks

## Protocol Configuration

Protocols are configured in `src/data/protocols.json`, which defines:

- Official protocol names
- Supported chains
- Contract addresses
- Other metadata

Example protocol configuration:

```json
{
  "protocols": [
    {
      "name": "Uniswap",
      "chains": {
        "1": {
          "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        }
      }
    },
    {
      "name": "Aave",
      "chains": {
        "1": {
          "lendingPool": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
        }
      }
    }
  ]
}
```

## ProtocolService

The `ProtocolService` serves as a central access point for protocol data:

```typescript
export class ProtocolService {
  /**
   * Returns protocol data from the JSON
   */
  public static getProtocolData() {
    return protocolsData.protocols;
  }

  /**
   * Builds a dependency graph from protocols.json
   */
  public static getDependencyGraph(): DependencyGraph {
    const graph: DependencyGraph = {};
    // Build dependency graph dynamically from protocol data
    // ...
    return graph;
  }

  /**
   * Normalizes protocol names to match exact case in protocols.json
   */
  public static getNormalizedProtocolName(name: string): string | undefined {
    // Create mapping on demand for case-insensitive lookups
    const protocolNameMap = new Map(
      this.getProtocolData().map((p) => [p.name.toLowerCase(), p.name])
    );

    return protocolNameMap.get(name.toLowerCase());
  }

  /**
   * Returns all protocol names from the configuration
   */
  public static getAllProtocolNames(): string[] {
    return this.getProtocolData().map((p) => p.name);
  }
}
```

## Protocol Detection Process

The protocol detection process follows these steps:

1. Load all protocol names from configuration
2. Convert both the protocol names and the input content to lowercase for case-insensitive matching
3. Find all protocols mentioned in the content
4. Normalize each detected protocol name to the official spelling in the configuration

### Implementation

The implementation in `SignalEvaluator` includes robust error handling:

```typescript
private detectProtocols(content: string): string[] {
  try {
    // Get all protocol names from the configuration
    const protocolNames = ProtocolService.getAllProtocolNames();

    if (!protocolNames || protocolNames.length === 0) {
      console.warn("No protocol names available from ProtocolService");
      return [];
    }

    // Convert to lowercase for matching
    const protocolNamesLower = protocolNames.map(name => name.toLowerCase());

    // Find matches in the content
    const matchedProtocols = protocolNamesLower.filter(name =>
      content.includes(name)
    );

    if (matchedProtocols.length === 0) {
      return [];
    }

    // Normalize protocol names and handle missing matches gracefully
    return matchedProtocols.map(match => {
      const normalized = ProtocolService.getNormalizedProtocolName(match);
      if (!normalized) {
        console.warn(`Could not normalize protocol name: ${match}`);
        return match; // Fall back to the matched name
      }
      return normalized;
    });
  } catch (error) {
    console.error("Error in protocol detection:", error);
    return []; // Return empty array on error
  }
}
```

## Error Handling

The protocol detection system includes multiple layers of error handling:

1. **Missing Protocol Configuration**: If `protocols.json` is missing or empty, warning logs are generated, and an empty array is returned
2. **Normalization Failure**: If a protocol name can't be normalized, the system logs a warning and falls back to the detected name
3. **Exception Handling**: All operations are wrapped in try-catch blocks to prevent crashes
4. **Defensive Coding**: Null checks and array length validation prevent issues with unexpected data

## Integration with State Machine

The protocol detection system integrates with the XState state machine through the `evaluateSignals` actor. This actor gracefully handles any errors in protocol detection, ensuring the state machine can continue operation even if protocol detection fails.

## Best Practices

When adding or modifying protocols:

1. Update `protocols.json` with the official protocol name and correct casing
2. Ensure all protocol references in the codebase use normalized names from `ProtocolService`
3. Avoid hardcoding protocol names in services or actors
4. Use the `detectProtocols` method in `SignalEvaluator` as a model for robust protocol detection in other services
