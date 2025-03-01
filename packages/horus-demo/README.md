# Horus DeFi Protection System

Horus is an AI-powered agent that monitors DeFi protocols for security threats and automatically takes protective actions to secure users' assets. The system uses state machine architecture to coordinate threat detection, analysis, and on-chain response.

## System Overview

Horus continuously polls for security signals (currently from Twitter) and uses a combination of keyword analysis and AI evaluation to detect potential threats to DeFi protocols. When a threat is detected, Horus analyzes the affected protocols and tokens, composes an action plan based on a dependency graph, and executes protective actions like withdrawals, swaps, or revocations on the blockchain.

## Architecture Design

The project follows a modular, service-oriented architecture built around a state machine core:

![Horus Architecture](https://i.imgur.com/YourDiagramLink.png)

### Core Components

#### 1. State Machine

At the heart of Horus is an xState-based state machine that orchestrates the entire workflow. The machine has six primary states:

- **idle**: Waiting for security signals
- **evaluating**: Analyzing signals for threats
- **processing**: Determining affected protocols and tokens
- **composing**: Creating an action plan
- **executing**: Performing on-chain transactions
- **completed**: Successfully executed actions
- **failed**: Error handling & recovery

#### 2. Models

The system uses strongly-typed data models to represent:

- **Signal**: Security information from external sources
- **Threat**: Analyzed security vulnerability with affected components
- **Action**: Protective measures to be taken (swap/withdraw/revoke)
- **Configuration**: Protocol and token information, dependency relationships
- **SignalEvaluationResult**: Standardized result type for signal evaluation with support for error reporting
- **Token**: Token metadata including name, symbol, decimal precision, and network addresses

#### 3. Services

Specialized services handle specific business logic:

- **SignalEvaluator**: Analyzes incoming signals for threats with robust error handling
- **ActionComposer**: Determines appropriate protective actions
- **ActionExecutor**: Performs actions on the blockchain
- **AgentService**: Integrates with AI for enhanced analysis
- **TwitterPoller**: Provides mock Twitter signals for testing
- **ProtocolService**: Manages protocol data and normalization for consistent protocol references
- **TokenService**: Centralizes token management, including detection, normalization, and address resolution

#### 4. Schemas

The system uses Zod schemas for runtime validation:

- **SignalEvaluationResultSchema**: Validates the structure of LLM responses for signal evaluation, ensuring they match the expected format with proper threat details. This ensures that any LLM-generated output can be safely parsed and used within the system.

#### 5. Configuration

Static configuration defines the DeFi ecosystem structure:

- **protocols.json**: Protocol metadata, contract addresses, and normalized naming
- **dependency_graph.json**: Maps protocols to their dependent tokens (dynamically built from protocols.json)
- **tokens.json**: Token details like decimals and addresses

## Workflow Process

1. **Signal Detection**: The TwitterPoller monitors for security alerts
2. **Threat Evaluation**: The SignalEvaluator analyzes signal content with robust error handling
3. **Threat Processing**: For confirmed threats, enhanced analysis is performed
4. **Action Composition**: The ActionComposer determines necessary protective steps
5. **Action Execution**: The ActionExecutor performs blockchain transactions
6. **Completion**: Results are recorded, and the system returns to idle

## Error Handling and Robustness

The system implements multiple layers of error handling to ensure robustness:

### 1. Protocol Detection and Normalization

Signal evaluation uses a robust protocol detection system that:

- Dynamically loads protocol names from configuration
- Normalizes protocol names to ensure consistency with the dependency graph
- Handles edge cases including missing protocols or failed normalization
- Provides detailed logging for debugging

### 2. Token Detection and Normalization

The system uses a comprehensive token handling system that:

- Dynamically loads token data from the `tokens.json` configuration
- Normalizes token symbols to ensure consistent references throughout the application
- Validates tokens before performing blockchain actions
- Resolves token addresses for specific chains from configuration
- Provides detailed error handling and fallbacks

```typescript
// Detect tokens in content with robust error handling
public static detectTokensInContent(content: string): string[] {
  if (!content) return [];

  try {
    const contentLower = content.toLowerCase();
    const allTokensLower = this.getAllTokenSymbolsLowercase();

    // Find matches in the content
    const matchedTokens = allTokensLower.filter(symbol =>
      contentLower.includes(symbol)
    );

    // Normalize token symbols with fallbacks
    return matchedTokens.map(match => {
      const normalized = this.getNormalizedTokenSymbol(match);
      return normalized || match; // Fallback to detected token if normalization fails
    });
  } catch (error) {
    console.error(`[TokenService] Error detecting tokens: ${error}`);
    return []; // Return empty array on error
  }
}

// Validate tokens before executing blockchain actions
try {
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

  // Get token address for the specific chain
  const tokenAddress = TokenService.getTokenAddress(
    normalizedToken,
    this.DEFAULT_CHAIN_ID
  );
} catch (error) {
  // Structured error handling
  console.error(`Error executing action for ${action.token}:`, error);
}
```

### 3. XState Actor Integration

The state machine actors are designed for maximum stability:

- Each actor provides meaningful error messages with service name prefixing
- Actors handle edge cases and provide fallbacks rather than crashing
- Return types are properly structured for state machine consumption
- Actors return formatted errors that the state machine can process

```typescript
const evaluateSignalsActor = fromPromise(
  async ({ input }): Promise<SignalEvaluationResult> => {
    // Input validation with helpful error message
    if (!input.context.currentSignal) {
      const error = new Error("No signal to evaluate");
      console.error(
        "[evaluateSignalsActor] Input validation failed:",
        error.message
      );
      throw error;
    }

    try {
      const result = await signalEvaluator.evaluateSignal(
        input.context.currentSignal
      );

      // Handle edge cases where fields might be missing
      if (result.isThreat && !result.threat) {
        console.warn(
          "[evaluateSignalsActor] Threat flagged but no threat details provided"
        );
        // Create a minimal threat object to prevent downstream errors
        return {
          isThreat: true,
          threat: {
            description: `Potential unnamed threat detected: ${input.context.currentSignal.content}`,
            affectedProtocols: [],
            affectedTokens: ["unknown"],
            chain: "ethereum",
            severity: "medium",
          },
        };
      }

      return result;
    } catch (error) {
      // Return a properly structured error result instead of throwing
      return {
        isThreat: false,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }
);
```

### 4. Structured Type System

The system uses a robust type system to ensure data consistency:

- Central type definitions are shared across the application
- The `SignalEvaluationResult` interface provides a standardized return format
- Error types are properly integrated into the type system
- Type assertions are used strategically to handle XState actor output types

## Key Design Patterns

### State Machine Pattern

Using xState provides a predictable, visual way to handle complex application flow. The state transitions create a clear audit trail of system behavior.

### Service Layer Pattern

Business logic is encapsulated in dedicated services with clear responsibilities, making the system modular and testable.

### Dependency Injection

Services are instantiated once and injected where needed, promoting singleton behavior and efficient resource usage.

### Command Pattern

Actions (withdraw/swap/revoke) are represented as command objects that can be composed, stored, and executed later.

### Configuration Service Pattern

Protocol and token data are managed through service objects that provide normalized access to configuration, enhancing maintainability and reducing hardcoded values.

## Implementation Details

### TypeScript Types

Strong typing ensures consistent data structures throughout the application:

```typescript
export interface Signal {
  source: SignalSource;
  content: string;
  timestamp: number;
}

export interface Threat {
  description: string;
  affectedProtocols: string[];
  affectedTokens: string[];
  chain: string;
  severity: SeverityLevel;
}

export interface SignalEvaluationResult {
  isThreat: boolean;
  threat?: Threat;
  error?: Error;
}

export interface Action {
  type: ActionType;
  protocol: string;
  token: string;
  params: Record<string, string | number | boolean>;
}
```

### State Machine Definition

The xState machine defines states, transitions, and context:

```typescript
export const horusMachine = setup({
  types: {
    context: {} as HorusContext,
    events: {} as HorusEvent,
  },
  // ... actions, guards ...
}).createMachine({
  id: "horus",
  initial: "idle",
  context: initialContext,
  states: {
    idle: {
      on: {
        SIGNAL_RECEIVED: {
          target: "evaluating",
          actions: "assignSignal",
        },
      },
    },
    // ... other states ...
  },
});
```

### Service Implementation

Each service has a clear, focused responsibility:

```typescript
// SignalEvaluator example
public async evaluateSignal(signal: Signal): Promise<{ isThreat: boolean; threat?: Threat }> {
  // Use AI or keyword analysis to evaluate the signal
  const content = signal.content.toLowerCase();
  const containsThreatKeywords = this.threatKeywords.some(
    keyword => content.includes(keyword.toLowerCase())
  );

  // ... protocol and token detection ...

  return {
    isThreat: true,
    threat: {
      // ... threat details ...
    }
  };
}
```

## Testing Approach

The project includes several types of tests:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing the full workflow with mocked services
3. **Mock Data**: Simulated Twitter data for testing without external dependencies

## Future Enhancements

- Replace mock Twitter implementation with real Twitter API
- Integrate full AgentKit implementation for AI analysis
- Add real blockchain interactions via ethers.js
- Implement multi-chain support for broader protection
- Create a monitoring dashboard for visualization

## Getting Started

1. Install dependencies:

   ```
   npm install
   ```

2. Run tests:

   ```
   npm test
   ```

3. Start the application:
   ```
   npm start
   ```

## Project Structure

```
horus-agent/
├── config/                   # Configuration files
│   ├── dependency_graph.json
│   ├── protocols.json
│   └── tokens.json
├── src/
│   ├── models/               # Type definitions
│   │   ├── types.ts
│   │   └── config.ts
│   ├── mock/                 # Test data
│   │   └── tweet-generator.ts
│   ├── services/             # Business logic
│   │   ├── signal-evaluator.ts
│   │   ├── action-composer.ts
│   │   ├── action-executor.ts
│   │   └── agent-service.ts
│   ├── state/                # State machine
│   │   ├── types.ts
│   │   ├── machine.ts
│   │   └── services.ts
│   └── index.ts              # Entry point
└── tests/                    # Test suite
    ├── machine.test.ts
    ├── twitter-service.test.ts
    └── integration.test.ts
```

## Technologies Used

- **xState**: State machine for workflow orchestration
- **TypeScript**: For type safety and developer experience
- **Vitest**: For testing
- **AgentKit** (planned): For AI-powered analysis
- **Ethers.js** (planned): For blockchain interactions
