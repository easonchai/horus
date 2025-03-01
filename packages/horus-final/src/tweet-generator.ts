import mockTweetsData from "./data/mockTweets.json";
import { Signal } from "./types";
import { getLogger } from "./utils/logger";

// Initialize logger for this component
const logger = getLogger("TwitterPoller");

export interface Tweet {
  id: string;
  content: string;
  timestamp: number;
}

// Load tweets from the JSON file
export const mockTweets: Tweet[] = mockTweetsData as Tweet[];

export class TwitterPoller {
  private callback: (signal: Signal) => Promise<void>;
  private interval: NodeJS.Timeout | null = null;
  private currentIndex = 0;
  private isProcessing = false;

  /**
   * Creates a new TwitterPoller instance
   * @param callback Async function that processes a signal and returns a Promise
   */
  constructor(callback: (signal: Signal) => Promise<void>) {
    this.callback = callback;
    logger.info(`TwitterPoller initialized with ${mockTweets.length} tweets`);
  }

  /**
   * Starts polling for tweets with a 30-second delay between processing
   * @param intervalMs Initial delay before starting (not used for subsequent processing)
   */
  start(intervalMs = 5000) {
    logger.info(`Starting TwitterPoller with 30-second delay between signals`);

    // Initial delay before starting
    this.interval = setTimeout(() => {
      this.processNextTweet();
    }, intervalMs);
  }

  /**
   * Stops the tweet polling
   */
  stop() {
    if (this.interval) {
      clearTimeout(this.interval);
      this.interval = null;
      logger.info("TwitterPoller stopped");
    }
  }

  /**
   * Processes the next tweet and schedules the next one after 30 seconds
   * @private
   */
  private async processNextTweet() {
    if (this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    try {
      if (this.currentIndex >= mockTweets.length) {
        logger.info("All tweets processed, resetting index to start over");
        this.currentIndex = 0;
      }

      const tweet = mockTweets[this.currentIndex++];
      logger.info(
        `Processing tweet ${tweet.id}: "${tweet.content.substring(0, 30)}..."`
      );

      const signal: Signal = {
        source: "twitter",
        content: tweet.content,
        timestamp: tweet.timestamp,
      };

      logger.debug(`Sending tweet ${tweet.id} as signal to callback`);

      // Process the current tweet
      await this.callback(signal);

      logger.info(`Finished processing tweet ${tweet.id}`);
    } catch (error) {
      logger.error("Error processing tweet:", error);
    } finally {
      this.isProcessing = false;

      // Schedule the next tweet processing after a 30-second delay
      logger.info("Waiting 30 seconds before processing the next signal...");
      this.interval = setTimeout(() => {
        this.processNextTweet();
      }, 30000); // 30 seconds
    }
  }
}
