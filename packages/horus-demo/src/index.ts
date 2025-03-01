import { createActor } from "xstate";
import { TwitterPoller } from "./mock/tweet-generator";
import { horusMachine } from "./state/machine";

console.log("Starting Horus DeFi Protection System...");

// Create the main Horus actor
const horusActor = createActor(horusMachine, {
  input: {
    signals: [],
    actionPlan: [],
    executionResults: [],
  },
});

// Subscribe to state changes
horusActor.subscribe((state) => {
  console.log(`[${new Date().toISOString()}] State: ${state.value}`);

  // Log context for specific states
  if (state.value === "evaluating") {
    console.log(`Evaluating signal: "${state.context.currentSignal?.content}"`);
  } else if (state.value === "processing") {
    console.log(
      `Processing threat: ${state.context.detectedThreat?.description}`
    );
  } else if (state.value === "composing") {
    console.log(
      `Composing actions for: ${state.context.detectedThreat?.affectedProtocols.join(
        ", "
      )}`
    );
  } else if (state.value === "executing") {
    console.log(`Executing ${state.context.actionPlan.length} actions`);
  } else if (state.value === "completed") {
    console.log(`Completed ${state.context.executionResults.length} actions`);
  } else if (state.value === "failed") {
    console.log(`Error: ${state.context.error?.message}`);
  }
});

// Start the Horus actor with error handling
try {
  horusActor.start();
  console.log("Horus actor started successfully");
} catch (error) {
  console.error("Failed to start Horus actor:", error);
  // Continue execution even if there's an error with the actor
}

// Create Twitter poller
const twitterPoller = new TwitterPoller((signal) => {
  console.log(`Received signal from Twitter: "${signal.content}"`);

  // Send the signal to the Horus actor
  try {
    horusActor.send({
      type: "SIGNAL_RECEIVED",
      signal,
    });
  } catch (error) {
    console.error("Error sending signal to Horus actor:", error);
  }
});

// Start polling for tweets
try {
  twitterPoller.start(5000); // Poll every 5 seconds
  console.log("Twitter poller started successfully");
} catch (error) {
  console.error("Failed to start Twitter poller:", error);
}

// Handle application shutdown
process.on("SIGINT", () => {
  console.log("Shutting down Horus...");
  twitterPoller.stop();
  process.exit(0);
});

// Handle uncaught exceptions to prevent app crash
process.on("uncaughtException", (error) => {
  console.error("Uncaught exception:", error);
  // Keep the application running despite the error
});

console.log("Horus is now monitoring for security threats...");
