# Horus Demo

A TypeScript package for demonstrating Horus functionality.

## Setup

This package is part of the Horus monorepo and uses:
- TypeScript for type-safe development
- mise for dependency management
- pnpm for package management
- tsup for bundling
- Vitest for testing

## Installation

From the root of the monorepo:

```bash
# Install dependencies for horus-demo only
pnpm install:demo

# Install dependencies for the horus package (if needed)
pnpm install:horus
```

## Development

```bash
# Start development mode with watch (horus-demo only)
pnpm dev

# Build the package
pnpm build

# Run tests
pnpm test

# Lint code
pnpm lint

# Run the horus package (if needed)
pnpm dev:horus

# Run development for all packages
pnpm dev:all
```

## Usage

```typescript
import { greet } from 'horus-demo';

// Use the package functionality
const message = greet('User'); // Returns "Hello, User!"
console.log(message);
```
