// The signal processor will take in signals for different sources and execute execute our agent logic.
// Currently only supporting twitter. We are using the twitter mock data polling for now

import { TwitterPoller } from "./tweet-generator";
import { Signal } from "./types";
import { getLogger } from "./utils/logger";

// Initialize logger for this component
const logger = getLogger("SignalProcessor");

export class SignalProcessor {
  private twitterPoller: TwitterPoller;
  private signalCallback: (signal: Signal) => Promise<void>;

  /**
   * Creates a new SignalProcessor instance
   * @param signalCallback Async function that processes a signal and returns a Promise
   */
  constructor(signalCallback: (signal: Signal) => Promise<void>) {
    this.signalCallback = signalCallback;

    // Initialize Twitter poller with a callback that processes signals
    this.twitterPoller = new TwitterPoller(async (signal) => {
      await this.processSignal(signal);
    });

    logger.info("SignalProcessor initialized");
  }

  /**
   * Start processing signals
   * @param intervalMs Polling interval in milliseconds
   */
  start(intervalMs = 5000): void {
    logger.info("Signal processor starting...");
    this.twitterPoller.start(intervalMs);
  }

  /**
   * Stop processing signals
   */
  stop(): void {
    logger.info("Signal processor stopping...");
    this.twitterPoller.stop();
  }

  /**
   * Process an incoming signal
   * @param signal The signal to process
   */
  private async processSignal(signal: Signal): Promise<void> {
    logger.info(
      `Processing signal from ${signal.source}: "${signal.content.substring(
        0,
        30
      )}..."`
    );

    try {
      // Apply any simple processing logic here
      // For now, just forward the signal to the callback
      await this.signalCallback(signal);
      logger.info(
        `Signal processing completed for: "${signal.content.substring(
          0,
          30
        )}..."`
      );
    } catch (error) {
      logger.error(`Error processing signal: ${error}`);
      // Even if there's an error, we consider the signal "processed" so we can move on
    }
  }
}
