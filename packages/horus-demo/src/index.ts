/**
 * Horus Demo
 *
 * A TypeScript package for demonstrating Horus functionality.
 */

import { showBanner, showShutdownBanner } from './ui';
import { TwitterPoller } from './utils/polling';


/**
 * Main function to demonstrate the package functionality
 */
export function main(): void {
  // Display the ASCII art banner
  showBanner('Twitter Security Monitoring Demo');

  const twitterPoller = new TwitterPoller((sig) => {
    console.log(`Received signal: ${JSON.stringify(sig)}`);
  });

  twitterPoller.start();

  // Setup graceful shutdown
  process.on('SIGINT', () => {
    showShutdownBanner();
    process.exit(0);
  });
}

// Allow running directly with Node.js
if (require.main === module) {
  main();
}
