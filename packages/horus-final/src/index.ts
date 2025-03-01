import { agent } from "./agent";
import { SignalProcessor } from "./signal-processor";
import { Signal } from "./types";
import { getLogger } from "./utils/logger";

// Initialize logger for this component
const logger = getLogger("Main");

logger.info("Hello World! Horus DeFi Protection System starting...");

// Create a signal processor
const signalProcessor = new SignalProcessor(async (signal: Signal) => {
  logger.info(
    `Received processed signal: "${signal.content.substring(0, 30)}..."`
  );

  try {
    // Pass the signal to our Agent for processing
    const result = await agent.processSignal(signal);
    logger.info("Agent analysis completed");
    logger.debug("Agent analysis result:", result.text);
    return result; // Return the result to indicate processing is complete
  } catch (error) {
    logger.error("Error processing signal with agent:", error);
    throw error; // Re-throw to indicate processing failed
  }
});

// Start processing signals
try {
  // Start with initial delay of 5 seconds, will then use 30-second delays between signals
  signalProcessor.start(20000);
  logger.info("Signal processor started successfully");
} catch (error) {
  logger.error("Failed to start signal processor:", error);
}

// Handle application shutdown
process.on("SIGINT", () => {
  logger.info("Shutting down Horus...");
  signalProcessor.stop();
  process.exit(0);
});

// Handle uncaught exceptions to prevent app crash
process.on("uncaughtException", (error) => {
  logger.error("Uncaught exception:", error);
  // Keep the application running despite the error
});

// Log that the application is ready
logger.info(
  "Horus DeFi Protection System is now running and monitoring for signals"
);
