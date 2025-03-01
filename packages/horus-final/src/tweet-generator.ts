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
  private tweetQueue: Tweet[] = [];
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
   * Starts polling for tweets at the specified interval
   * @param intervalMs Interval in milliseconds between tweet polls
   */
  start(intervalMs = 10000) {
    logger.info(`Starting TwitterPoller with interval of ${intervalMs}ms`);

    // Initial processing to start the queue
    this.queueNextTweet();

    // Set up interval to add tweets to the queue
    this.interval = setInterval(() => {
      this.queueNextTweet();
    }, intervalMs);
  }

  /**
   * Stops the tweet polling
   */
  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      logger.info("TwitterPoller stopped");
    }
  }

  /**
   * Queues the next tweet for processing
   * @private
   */
  private queueNextTweet() {
    if (this.currentIndex < mockTweets.length) {
      const tweet = mockTweets[this.currentIndex++];
      logger.debug(
        `Queuing tweet ${tweet.id}: "${tweet.content.substring(0, 30)}..."`
      );

      this.tweetQueue.push(tweet);
      logger.info(
        `Tweet ${tweet.id} added to queue. Queue size: ${this.tweetQueue.length}`
      );

      // Process the queue if not already processing
      if (!this.isProcessing) {
        this.processQueue();
      }
    } else {
      logger.info("All tweets processed, resetting index to start over");
      this.currentIndex = 0; // Reset to start over when all tweets are processed

      // Queue the first tweet again after reset
      if (mockTweets.length > 0) {
        const tweet = mockTweets[this.currentIndex++];
        this.tweetQueue.push(tweet);

        // Process the queue if not already processing
        if (!this.isProcessing) {
          this.processQueue();
        }
      }
    }
  }

  /**
   * Processes tweets in the queue sequentially
   * @private
   */
  private async processQueue() {
    if (this.tweetQueue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    try {
      const tweet = this.tweetQueue.shift()!;
      logger.info(
        `Processing tweet ${tweet.id} from queue. Remaining in queue: ${this.tweetQueue.length}`
      );

      const signal: Signal = {
        source: "twitter",
        content: tweet.content,
        timestamp: tweet.timestamp,
      };

      logger.debug(`Sending tweet ${tweet.id} as signal to callback`);

      // Wait for the callback to complete before processing the next tweet
      await this.callback(signal);

      logger.info(`Finished processing tweet ${tweet.id}`);
    } catch (error) {
      logger.error("Error processing tweet:", error);
    } finally {
      this.isProcessing = false;

      // Process the next tweet in the queue if any
      if (this.tweetQueue.length > 0) {
        this.processQueue();
      } else {
        logger.debug("Queue is empty, waiting for new tweets");
      }
    }
  }
}
