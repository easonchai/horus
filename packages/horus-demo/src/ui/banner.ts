/**
 * ASCII Art Banner for Horus Security Monitoring
 * 
 * This module provides functions to display a stylized ASCII art banner in the terminal
 */

import figlet from 'figlet';
import chalk from 'chalk';

/**
 * Display the Horus ASCII art banner with optional subtitle
 * @param subtitle Optional subtitle to display below the banner
 */
export function showBanner(subtitle?: string): void {
  // Generate ASCII art for "HORUS"
  const asciiArt = figlet.textSync('HORUS', {
    font: 'Standard',
    horizontalLayout: 'default',
    verticalLayout: 'default'
  });
  
  // Display the banner with eye symbol
  console.log('\n');
  console.log(chalk.yellow(asciiArt));
  console.log(chalk.yellow('  👁️  Security Monitoring System  👁️'));
  console.log('\n');
  
  // Display subtitle if provided
  if (subtitle) {
    console.log(chalk.cyan(`  ${subtitle}`));
    console.log('\n');
  }
  
  // Display info line
  const timestamp = new Date().toLocaleTimeString();
  console.log(chalk.gray(`  Started at ${timestamp}`));
  console.log(chalk.gray('  ----------------------------------------'));
  console.log('\n');
}

/**
 * Display a shutdown banner
 */
export function showShutdownBanner(): void {
  console.log('\n');
  console.log(chalk.yellow('  HORUS Security Monitoring Shutting Down'));
  console.log(chalk.gray(`  Ended at ${new Date().toLocaleTimeString()}`));
  console.log('\n');
}
