import { SignalProcessor } from "./signal-processor";
import { Signal } from "./types";

console.log("Hello World! Horus DeFi Protection System starting...");

// Create a signal processor
const signalProcessor = new SignalProcessor((signal: Signal) => {
  console.log(`Received processed signal: "${signal.content}"`);
  // In the future, this is where we would pass the signal to an agent
});

// Start processing signals
try {
  signalProcessor.start(5000); // Poll every 5 seconds
  console.log("Signal processor started successfully");
} catch (error) {
  console.error("Failed to start signal processor:", error);
}

// Handle application shutdown
process.on("SIGINT", () => {
  console.log("Shutting down Horus...");
  signalProcessor.stop();
  process.exit(0);
});

// Handle uncaught exceptions to prevent app crash
process.on("uncaughtException", (error) => {
  console.error("Uncaught exception:", error);
  // Keep the application running despite the error
});
