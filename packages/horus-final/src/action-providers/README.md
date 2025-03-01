# Action Providers

This directory contains action providers that enable the Horus DeFi Protection System to interact with various DeFi protocols. These providers implement the `ActionProvider` interface from `@coinbase/agentkit` and expose methods that can be called by the AI agent to perform protective actions.

## Available Providers

### RevokeProvider (`revoke-provider.ts`)

The `RevokeProvider` handles token approval revocations, helping users protect their assets by removing permissions from potentially malicious contracts.

#### Actions:

- **`revoke-token-approval`**: Revokes a token approval for a specific contract address.
  - Parameters: `tokenSymbol` (token to revoke approval for), `spenderAddress` (contract to revoke from)
- **`check-token-approvals`**: Checks what contracts have approval to spend a specific token.
  - Parameters: `tokenSymbol` (token to check approvals for)

### SwapProvider (`swap-provider.ts`)

The `SwapProvider` enables emergency swaps between tokens, allowing users to quickly move assets to safer tokens in case of a security threat.

#### Actions:

- **`swap-max-balance`**: Swaps the maximum balance of a token for another token (currently USDC to USDT or vice versa).
  - Parameters: `fromToken` (token to swap from)

### WithdrawalProvider (`withdrawal-provider.ts`)

The `WithdrawalProvider` facilitates withdrawals from DeFi protocols, allowing users to quickly remove their assets in emergency situations.

#### Actions:

- **`withdraw-from-beefy`**: Withdraws funds from a Beefy Finance vault.
  - Parameters: `vaultType` (type of vault), `tokenId` (position ID)
- **`withdraw-from-uniswap`**: Withdraws liquidity from a Uniswap V3 position.
  - Parameters: `positionId` (NFT position ID), `percentage` (liquidity percentage to withdraw)
- **`emergency-withdraw-all`**: Performs an emergency withdrawal from all connected protocols.
  - Parameters: `reason` (optional explanation), `prioritizeSafety` (whether to prioritize safety over efficiency)

## Common Features

All action providers include:

1. **Wallet Provider Integration**: Each action takes a `WalletProvider` as the first parameter, allowing direct interaction with the user's wallet.

2. **Network Support**: Each provider implements a `supportsNetwork` method that checks if the current network is supported (currently Base Sepolia).

3. **Error Handling**: All actions include proper error handling and logging.

4. **Response Formatting**: Actions return formatted markdown strings that clearly explain the action taken and its results.

## Usage Example

```typescript
import { agent } from "../agent";
import { Signal } from "../types";

// When a security signal is received
const signal: Signal = {
  source: "twitter",
  content:
    "Warning: Protocol X has been compromised. Revoke approvals immediately!",
  timestamp: Date.now(),
};

// Process the signal
const analysis = await agent.processSignal(signal);

// The agent may recommend or execute actions based on the analysis
// For example, it might call the revoke-token-approval action
```

## Implementing New Providers

To add a new action provider:

1. Create a new file in this directory (e.g., `new-provider.ts`)
2. Extend the `ActionProvider<WalletProvider>` class
3. Implement actions using the `@CreateAction` decorator
4. Include proper logging with the logger utility
5. Export a factory function that creates a new instance of your provider

Example structure:

```typescript
import {
  ActionProvider,
  CreateAction,
  WalletProvider,
} from "@coinbase/agentkit";
import "reflect-metadata";
import { z } from "zod";
import { getLogger } from "../utils/logger";

const logger = getLogger("NewProvider");

const actionSchema = z.object({
  // Define your parameters here
});

export class NewProvider extends ActionProvider<WalletProvider> {
  constructor() {
    super("new-provider", []);
    logger.info("NewProvider initialized");
  }

  @CreateAction({
    name: "new-action",
    description: "Description of what this action does",
    schema: actionSchema,
  })
  async newAction(
    walletProvider: WalletProvider,
    args: z.infer<typeof actionSchema>
  ): Promise<string> {
    // Implement your action logic here
  }

  supportsNetwork = (network: Network) => {
    // Define network support logic
  };
}

export const newProvider = () => new NewProvider();
```
