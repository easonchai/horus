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
  private callback: (signal: Signal) => void;
  private interval: NodeJS.Timeout | null = null;
  private currentIndex = 0;

  constructor(callback: (signal: Signal) => void) {
    this.callback = callback;
    logger.info(`TwitterPoller initialized with ${mockTweets.length} tweets`);
  }

  start(intervalMs = 10000) {
    logger.info(`Starting TwitterPoller with interval of ${intervalMs}ms`);
    this.interval = setInterval(() => {
      if (this.currentIndex < mockTweets.length) {
        const tweet = mockTweets[this.currentIndex++];
        logger.debug(
          `Processing tweet ${tweet.id}: "${tweet.content.substring(0, 30)}..."`
        );

        const signal: Signal = {
          source: "twitter",
          content: tweet.content,
          timestamp: tweet.timestamp,
        };

        this.callback(signal);
        logger.info(`Sent tweet ${tweet.id} as signal to callback`);
      } else {
        logger.info("All tweets processed, resetting index to start over");
        this.currentIndex = 0; // Reset to start over when all tweets are processed
      }
    }, intervalMs);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      logger.info("TwitterPoller stopped");
    }
  }
}
