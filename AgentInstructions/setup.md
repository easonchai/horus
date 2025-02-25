# Project Setup Documentation

## Tools and Versions

- Python: 3.10.12 (managed by mise)
- Node.js: 22.14.0 LTS (managed by mise)
- Package Manager: pnpm 8.15.1
- Python Package Manager: Poetry
- Monorepo Tool: Turbo

## Project Structure

```
ethDenver2025/
├── .mise.toml          # Python and Node.js version management
├── turbo.json          # Turbo configuration
├── package.json        # Root package configuration
├── packages/
│   └── horus/         # Main Python package
│       ├── pyproject.toml
│       └── horus/
│           ├── __init__.py
│           └── main.py
└── AgentInstructions/
    └── setup.md       # This file
```

## Setup Instructions

1. Install mise if not already installed:
   ```bash
   curl https://mise.run | sh
   ```

2. Install Node.js and Python:
   ```bash
   mise install
   ```

3. Install pnpm:
   ```bash
   npm install -g pnpm
   ```

4. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

5. Install dependencies:
   ```bash
   pnpm install
   cd packages/horus && poetry install
   ```

## Running the Project

From the root directory:
```bash
pnpm dev
```

This will run the Horus application which currently outputs "Hello from Horus!"
