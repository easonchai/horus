// The signal processor will take in signals for different sources and execute execute our agent logic.
// Currently only supporting twitter. We are using the twitter mock data polling for now

import { TwitterPoller } from "./tweet-generator";
import { Signal } from "./types";

export class SignalProcessor {
  private twitterPoller: TwitterPoller;
  private signalCallback: (signal: Signal) => void;

  constructor(signalCallback: (signal: Signal) => void) {
    this.signalCallback = signalCallback;

    // Initialize Twitter poller with a callback that processes signals
    this.twitterPoller = new TwitterPoller((signal) => {
      this.processSignal(signal);
    });
  }

  /**
   * Start processing signals
   * @param intervalMs Polling interval in milliseconds
   */
  start(intervalMs = 5000): void {
    console.log("Signal processor starting...");
    this.twitterPoller.start(intervalMs);
  }

  /**
   * Stop processing signals
   */
  stop(): void {
    console.log("Signal processor stopping...");
    this.twitterPoller.stop();
  }

  /**
   * Process an incoming signal
   * @param signal The signal to process
   */
  private processSignal(signal: Signal): void {
    console.log(`Processing signal from ${signal.source}: "${signal.content}"`);

    // Apply any simple processing logic here
    // For now, just forward the signal to the callback
    this.signalCallback(signal);
  }
}
