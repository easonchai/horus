# Horus Security Monitoring Agent

Horus is a security monitoring tool that watches for threats and can automatically take protective actions like withdrawing funds or revoking permissions when serious threats are detected.

## Table of Contents

- [Horus Security Monitoring Agent](#horus-security-monitoring-agent)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation Guide](#installation-guide)
    - [Installing mise](#installing-mise)
      - [macOS](#macos)
      - [Linux/WSL](#linuxwsl)
    - [Installing Poetry](#installing-poetry)
      - [Install Poetry](#install-poetry)
    - [Setting up the Project](#setting-up-the-project)
  - [Project Structure](#project-structure)
  - [Running the Application](#running-the-application)
  - [Development Commands](#development-commands)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
      - ["Command not found" after installation](#%22command-not-found%22-after-installation)
      - [Node.js version conflicts](#nodejs-version-conflicts)
      - [Python dependency issues](#python-dependency-issues)
      - [Need to update pnpm](#need-to-update-pnpm)

## Prerequisites

Before you begin, make sure you have:

- A computer with macOS, Linux, or WSL on Windows
- Basic familiarity with terminal/command line
- Git installed (for cloning the repository)

## Installation Guide

### Installing mise

[mise](https://github.com/jdx/mise) is a unified runtime version manager (similar to asdf, nvm, or pyenv) that helps manage multiple language runtimes like Node.js and Python.

#### macOS

Using Homebrew:

```bash
brew install mise
```

#### Linux/WSL

```bash
curl https://mise.run | sh
```

After installation, add mise to your shell:

```bash
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
# Or for zsh
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc
```

Restart your terminal or run `source ~/.bashrc` (or `~/.zshrc`) to apply changes.

### Installing Poetry

[Poetry](https://python-poetry.org/) is a tool for dependency management and packaging in Python. It manages project dependencies, virtual environments, and package building.

#### Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH:

```bash
# For bash
echo 'export PATH="$HOME/.poetry/bin:$PATH"' >> ~/.bashrc
# For zsh
echo 'export PATH="$HOME/.poetry/bin:$PATH"' >> ~/.zshrc
```

Restart your terminal or run `source ~/.bashrc` (or `~/.zshrc`) to apply changes.

### Setting up the Project

1. Clone the repository:

```bash
git clone https://github.com/easonchai/horus.git
cd horus
```

2. Let mise install required runtimes (Node.js, Python):

```bash
mise install
```

This will automatically install the exact versions of Node.js and Python specified in the `.mise.toml` configuration file.

3. Install Node.js dependencies:

```bash
mise exec -- npm install -g pnpm
mise exec -- pnpm install
```

This installs pnpm (a fast, disk space efficient package manager) and uses it to install the project's Node.js dependencies.

4. Install Python dependencies for the Horus package:

```bash
mise exec -- pnpm install:horus
```

5. Install TypeScript dependencies for the Horus Demo package (if needed):

```bash
mise exec -- pnpm install:demo
```

## Project Structure

This repository is a monorepo containing multiple packages:

- **horus**: The main Python-based security monitoring agent
- **horus-demo**: A TypeScript-based demonstration package

Each package has its own README with specific instructions.

## Running the Application

To run the Horus security monitoring agent:

```bash
mise exec -- pnpm dev:horus
```

To run the Horus Demo application:

```bash
mise exec -- pnpm dev
```

To run all packages:

```bash
mise exec -- pnpm dev:all
```

## Development Commands

Here are some useful commands for development:

```bash
# Run tests for horus-demo
mise exec -- pnpm test

# Lint code for horus-demo
mise exec -- pnpm lint

# Build the horus-demo package
mise exec -- pnpm build

# Run the horus package
mise exec -- pnpm dev:horus

# Run the original horus development mode
mise exec -- pnpm dev:original
```

## Troubleshooting

### Common Issues

#### "Command not found" after installation

If you encounter "command not found" errors after installing mise or poetry:

- Make sure you've added them to your PATH and restarted your terminal
- Check installation logs for any errors
- Try running with the full path (e.g., `~/.mise/bin/mise` or `~/.poetry/bin/poetry`)

#### Node.js version conflicts

If you have issues with Node.js versions:

```bash
# Verify mise is using the correct version
mise exec -- node --version
# Should match the version in .mise.toml
```

#### Python dependency issues

If you encounter Python dependency issues:

```bash
# Clean and reinstall dependencies
mise exec -- poetry lock --no-update
mise exec -- poetry install
```

#### Need to update pnpm

If you need to update pnpm to the latest version:

```bash
mise exec -- npm add -g pnpm@latest
```

For additional help, please open an issue on our GitHub repository.
