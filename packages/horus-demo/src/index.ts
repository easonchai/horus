/**
 * Horus Demo
 * 
 * A TypeScript package for demonstrating Horus functionality.
 */

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
  console.log(greet('Horus'));
}

// Allow running directly with Node.js
if (require.main === module) {
  main();
}
