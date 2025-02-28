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

#### 3. Services

Specialized services handle specific business logic:

- **SignalEvaluator**: Analyzes incoming signals for threats
- **ActionComposer**: Determines appropriate protective actions
- **ActionExecutor**: Performs actions on the blockchain
- **AgentService**: Integrates with AI for enhanced analysis
- **TwitterPoller**: Provides mock Twitter signals for testing

#### 4. Configuration

Static configuration defines the DeFi ecosystem structure:

- **dependency_graph.json**: Maps protocols to their dependent tokens
- **protocols.json**: Protocol metadata and contract addresses
- **tokens.json**: Token details like decimals and addresses

## Workflow Process

1. **Signal Detection**: The TwitterPoller monitors for security alerts
2. **Threat Evaluation**: The SignalEvaluator analyzes signal content
3. **Threat Processing**: For confirmed threats, enhanced analysis is performed
4. **Action Composition**: The ActionComposer determines necessary protective steps
5. **Action Execution**: The ActionExecutor performs blockchain transactions
6. **Completion**: Results are recorded, and the system returns to idle

## Key Design Patterns

### State Machine Pattern

Using xState provides a predictable, visual way to handle complex application flow. The state transitions create a clear audit trail of system behavior.

### Service Layer Pattern

Business logic is encapsulated in dedicated services with clear responsibilities, making the system modular and testable.

### Dependency Injection

Services are instantiated once and injected where needed, promoting singleton behavior and efficient resource usage.

### Command Pattern

Actions (withdraw/swap/revoke) are represented as command objects that can be composed, stored, and executed later.

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

export interface Action {
  type: ActionType;
  protocol: string;
  token: string;
  params: Record<string, any>;
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
