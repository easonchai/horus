# Action Providers

This directory contains the action providers used by the Horus DeFi Protection system. Each provider implements specific functionality for interacting with DeFi protocols.

## Available Providers

### SwapProvider

Provides functionality for swapping tokens on decentralized exchanges, primarily Uniswap.

- `swapMaxBalance` - Swaps the maximum balance of a token to another token.

### RevokeProvider

Provides functionality for revoking token approvals from DeFi protocols.

- `revokeTokenApproval` - Revokes approval for a specific contract to spend a token.
- `checkTokenApprovals` - Checks all active token approvals for a specific token.

### WithdrawalProvider

A powerful and flexible provider for executing withdrawals from any DeFi contract.

- `withdraw` - Universal withdrawal function that can be used with any contract.
  - Supports customizable transaction parameters
  - Handles a wide variety of withdrawal patterns
  - Provides real transaction execution (not just simulation)
  - Supports confirmation tracking and callback notifications

## Implementation Notes

### Using the WithdrawalProvider

The `WithdrawalProvider` is designed to be a universal withdrawal solution for any DeFi protocol. It accepts a flexible set of parameters that can be adapted to any contract's withdrawal function.

Example usage:

```typescript
const result = await agent.execute({
  provider: "withdrawal-provider",
  action: "withdraw",
  args: {
    contractAddress: "0x1234...",
    protocol: "uniswap",
    functionName: "withdraw",
    args: [tokenId],
    description: "Withdraw liquidity from Uniswap V3 position",
  },
});
```

Parameters can be customized based on the specific protocol requirements, including:

- Contract identification (`contractAddress`, `protocol`)
- Function details (`functionName`, `functionSignature`, `abi`)
- Function arguments (`args`, `tokenId`, `percentage`)
- Transaction parameters (`value`, `gasLimit`, `maxFeePerGas`)
- Confirmation settings (`waitForConfirmation`, `confirmations`)
- Callback notifications (`callbackUrl`)
- Additional context (`metadata`)

See the withdrawal-provider.ts file for the full schema and implementation details.

## Creating a New Provider

To create a new provider, use the following template:

```typescript
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
