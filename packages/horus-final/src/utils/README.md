# Utility Modules

This directory contains utility modules that provide common functionality used throughout the Horus DeFi Protection System.

## Logger (`logger.ts`)

The `logger.ts` module provides a comprehensive logging system with configurable log levels, timestamps, and colored output. This logger should be used instead of direct `console.log` calls to ensure consistent logging across the application.

### Features

- Four log levels: DEBUG, INFO, WARN, and ERROR
- Colored console output for better visibility
- Optional timestamps
- Source context tracking
- Centralized log level configuration

### Usage

```typescript
import { getLogger, setLogLevel, LogLevel } from "../utils/logger";

// Create a logger for your component
const logger = getLogger("ComponentName");

// Log at different levels
logger.debug("Detailed debug information");
logger.info("General information message");
logger.warn("Warning condition occurred");
logger.error("Error condition", new Error("Something went wrong"));

// Set global log level (can also be set via environment variable)
setLogLevel(LogLevel.DEBUG); // Show all logs
setLogLevel(LogLevel.INFO); // Show INFO, WARN, ERROR logs
setLogLevel(LogLevel.WARN); // Show WARN, ERROR logs
setLogLevel(LogLevel.ERROR); // Show only ERROR logs
```

### Configuration

The logger can be configured globally:

```typescript
import { configureLogger } from "../utils/logger";

configureLogger({
  minLevel: LogLevel.INFO, // Minimum log level to display
  showTimestamp: true, // Show timestamps in log output
  useColors: true, // Use colored output
});
```

### Environment Variables

The logger respects the `LOG_LEVEL` environment variable, which can be set to:

- `0`: DEBUG (show all logs)
- `1`: INFO (default)
- `2`: WARN
- `3`: ERROR

Example in `.env` file:

```
LOG_LEVEL=0  # Show all logs including debug
```

### Best Practices

1. **Create Component-Specific Loggers**: Use a unique logger for each component/module.

   ```typescript
   const logger = getLogger("AgentService");
   ```

2. **Choose Appropriate Log Levels**:

   - `DEBUG`: Detailed diagnostic information, helpful for development
   - `INFO`: Notable events during normal operation
   - `WARN`: Warning conditions that don't prevent normal operation
   - `ERROR`: Error conditions that might require attention

3. **Include Contextual Information**: Provide enough context to understand the log entry.

   ```typescript
   logger.info(`Processing signal: ${signalId} from source: ${source}`);
   ```

4. **Log Errors Properly**: Include the error object when logging errors.

   ```typescript
   try {
     // Some operation
   } catch (error) {
     logger.error("Failed to process transaction", error);
   }
   ```

5. **Be Concise**: Keep log messages clear and to the point.
