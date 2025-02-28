/**
 * Horus Demo
 * 
 * A TypeScript package for demonstrating Horus functionality.
 */

import { showBanner, showShutdownBanner } from './ui';

/**
 * Example function that returns a greeting message
 * @param name The name to greet
 * @returns A greeting message
 */
export function greet(name: string = 'world'): string {
  return `Hello, ${name}!`;
}

/**
 * Main function to demonstrate the package functionality
 */
export function main(): void {
  // Display the ASCII art banner
  showBanner('Twitter Security Monitoring Demo');
  
  console.log(greet('Horus'));
  
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
