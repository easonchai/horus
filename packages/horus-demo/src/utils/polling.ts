import mockTweets from "../data/mockTweets.json";
import { Signal } from "../types";

interface Tweet {
  content: string;
  timestamp: number;
}

export class TwitterPoller {
  private callback: (signal: Signal) => void;
  private interval: NodeJS.Timeout | null = null;
  private currentIndex = 0;

  constructor(callback: (signal: Signal) => void) {
    this.callback = callback;
  }

  start(intervalMs = 10000) {
    this.interval = setInterval(() => {
      const tweets = mockTweets as Tweet[];
      if (this.currentIndex < tweets.length) {
        const tweet = tweets[this.currentIndex++];
        const signal: Signal = {
          source: "twitter",
          content: tweet.content,
          timestamp: tweet.timestamp,
        };
        this.callback(signal);
      }
    }, intervalMs);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }
}
