import { Signal } from '../models/types';

export interface Tweet {
  content: string;
  timestamp: number;
}

// Mock tweets for testing
export const mockTweets: Tweet[] = [
  {
    content: 'URGENT: Security vulnerability found in Uniswap V3 smart contract. Users advised to withdraw immediately.',
    timestamp: Date.now() - 3600000 // 1 hour ago
  },
  {
    content: 'Breaking: Aave protocol pausing withdrawals due to suspicious activity.',
    timestamp: Date.now() - 2400000 // 40 minutes ago
  },
  {
    content: 'Alert: Potential exploit discovered in Curve Finance. Investigating.',
    timestamp: Date.now() - 1800000 // 30 minutes ago
  },
  {
    content: 'False alarm: Previous reports about Uniswap were incorrect. No action needed.',
    timestamp: Date.now() - 1200000 // 20 minutes ago
  },
  {
    content: 'Security Advisory: New phishing attacks targeting DeFi users. Be vigilant.',
    timestamp: Date.now() - 600000 // 10 minutes ago
  }
];

export class TwitterPoller {
  private callback: (signal: Signal) => void;
  private interval: NodeJS.Timeout | null = null;
  private currentIndex = 0;

  constructor(callback: (signal: Signal) => void) {
    this.callback = callback;
  }

  start(intervalMs = 10000) {
    this.interval = setInterval(() => {
      const tweets = mockTweets;
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
