/**
 * Logger Module
 *
 * A simple, configurable logging utility for the Horus DeFi Protection System.
 * This module provides standardized logging with different levels of severity,
 * timestamps, and source context.
 */

// Log levels in order of increasing severity
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

// Global configuration
const config = {
  // Minimum log level to display (can be overridden via environment)
  minLevel: process.env.LOG_LEVEL
    ? parseInt(process.env.LOG_LEVEL)
    : LogLevel.INFO,
  // Whether to include timestamps in logs
  showTimestamp: true,
  // Whether to enable colored output (for supported terminals)
  enableColors: true,
};

// ANSI color codes for terminal output
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  debug: "\x1b[36m", // cyan
  info: "\x1b[32m", // green
  warn: "\x1b[33m", // yellow
  error: "\x1b[31m", // red
  timestamp: "\x1b[2m\x1b[37m", // dim white
};

/**
 * Logger class providing structured logging capabilities
 */
export class Logger {
  private source: string;

  /**
   * Create a new logger instance
   *
   * @param source - The source/context identifier for this logger
   */
  constructor(source: string) {
    this.source = source;
  }

  /**
   * Format a log message with timestamp and source
   *
   * @param level - The severity level of the log
   * @param message - The message to log
   * @returns Formatted log message
   */
  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = config.showTimestamp
      ? `${
          config.enableColors ? colors.timestamp : ""
        }[${new Date().toISOString()}]${
          config.enableColors ? colors.reset : ""
        } `
      : "";

    const levelName = LogLevel[level];
    let levelFormatted = levelName;

    if (config.enableColors) {
      let color = "";
      switch (level) {
        case LogLevel.DEBUG:
          color = colors.debug;
          break;
        case LogLevel.INFO:
          color = colors.info;
          break;
        case LogLevel.WARN:
          color = colors.warn;
          break;
        case LogLevel.ERROR:
          color = colors.error;
          break;
      }
      levelFormatted = `${color}${levelName}${colors.reset}`;
    }

    return `${timestamp}${levelFormatted} [${this.source}]: ${message}`;
  }

  /**
   * Log a debug message
   * @param message - The message to log
   * @param data - Optional data to include (will be JSON stringified)
   */
  debug(message: string, data?: any): void {
    if (config.minLevel <= LogLevel.DEBUG) {
      const formattedMessage = this.formatMessage(LogLevel.DEBUG, message);
      console.debug(formattedMessage, data !== undefined ? data : "");
    }
  }

  /**
   * Log an informational message
   * @param message - The message to log
   * @param data - Optional data to include (will be JSON stringified)
   */
  info(message: string, data?: any): void {
    if (config.minLevel <= LogLevel.INFO) {
      const formattedMessage = this.formatMessage(LogLevel.INFO, message);
      console.info(formattedMessage, data !== undefined ? data : "");
    }
  }

  /**
   * Log a warning message
   * @param message - The message to log
   * @param data - Optional data to include (will be JSON stringified)
   */
  warn(message: string, data?: any): void {
    if (config.minLevel <= LogLevel.WARN) {
      const formattedMessage = this.formatMessage(LogLevel.WARN, message);
      console.warn(formattedMessage, data !== undefined ? data : "");
    }
  }

  /**
   * Log an error message
   * @param message - The message to log
   * @param error - Optional error object or any data to include
   */
  error(message: string, error?: any): void {
    if (config.minLevel <= LogLevel.ERROR) {
      const formattedMessage = this.formatMessage(LogLevel.ERROR, message);
      console.error(formattedMessage, error !== undefined ? error : "");
    }
  }
}

/**
 * Get a Logger instance for the specified source
 *
 * @param source - The source/context for the logger
 * @returns A Logger instance
 *
 * @example
 * ```typescript
 * // Get a logger for the agent module
 * const logger = getLogger('agent');
 *
 * // Log messages at different levels
 * logger.debug('Initializing agent with parameters', { param1: 'value1' });
 * logger.info('Agent initialized successfully');
 * logger.warn('Using fallback configuration');
 * logger.error('Failed to connect to service', error);
 * ```
 */
export function getLogger(source: string): Logger {
  return new Logger(source);
}

/**
 * Set the global minimum log level
 *
 * @param level - The minimum log level to display
 */
export function setLogLevel(level: LogLevel): void {
  config.minLevel = level;
}

/**
 * Configure logger settings
 *
 * @param options - Configuration options to apply
 */
export function configureLogger(options: {
  minLevel?: LogLevel;
  showTimestamp?: boolean;
  enableColors?: boolean;
}): void {
  if (options.minLevel !== undefined) config.minLevel = options.minLevel;
  if (options.showTimestamp !== undefined)
    config.showTimestamp = options.showTimestamp;
  if (options.enableColors !== undefined)
    config.enableColors = options.enableColors;
}

// Export a default logger for quick access
export default getLogger("app");
