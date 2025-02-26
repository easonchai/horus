# Horus Security Monitoring Agent

Horus is a security monitoring tool that watches for threats and can automatically take protective actions like withdrawing funds or revoking permissions when serious threats are detected.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Installing mise](#installing-mise)
- [Installing Poetry](#installing-poetry)
- [Setting up the Project](#setting-up-the-project)
- [Running the Application](#running-the-application)
- [Development Commands](#development-commands)
- [Troubleshooting](#troubleshooting)

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
git clone https://github.com/your-organization/horus.git
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

4. Install Python dependencies via Poetry:

```bash
mise exec -- poetry install
```

This sets up a virtual environment and installs all Python dependencies defined in the pyproject.toml file.

## Running the Application

To run the Horus security monitoring agent:

```bash
mise exec -- pnpm dev
```

This will start the development server with the correct Node.js version and environment.

## Development Commands

Here are some useful commands for development:

```bash
# Run tests
mise exec -- pnpm test

# Lint code
mise exec -- pnpm lint

# Build the application
mise exec -- pnpm build
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
