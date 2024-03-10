# Code Review Bot

## Overview

The Code Review Bot automates code reviews using OpenAI's powerful code analysis capabilities, integrated seamlessly with GitHub. Designed to support both GitHub Cloud and Enterprise instances, it offers flexible operation modes: as a standalone daemon service accepting webhook events or directly within GitHub Actions for on-demand code reviews. This versatility makes it suitable for organizations of any size, aiming to enhance their code quality with AI-driven insights.

## Features

- **Flexible Operation Modes**: Run as a standalone daemon service or integrate with GitHub Actions.
- **Support for Multiple Languages**: Customizable settings for Python, JavaScript, and more.
- **Repository-Specific Configurations**: Tailor code review settings on a per-repository basis.
- **Security-First Design**: IP whitelisting and rate limiting to ensure safe operation.
- **Extensible and Customizable**: Easy to extend support for additional programming languages and GitHub Enterprise configurations.

## Getting Started

### Prerequisites

- Python 3.7+
- FastAPI
- Uvicorn (for running FastAPI)
- PyYAML (for configuration parsing)
- Install other dependencies by running `pip install -r requirements.txt`.

### Installation

1. Clone this repository to your server or local machine.
2. Navigate to the cloned directory and install the required Python dependencies.

### Configuration

Configure the bot by editing the `config.yml` file located in the root directory. This file controls various aspects of the bot's operation, including OpenAI integration, GitHub settings, and operational modes.

#### Key Configuration Sections:

- `operation_mode`: Choose between `"daemon"` for a webhook-based service or `"github_action"` for running within GitHub Actions.
- `openai`: Set your OpenAI API key and default model settings.
- `github`: Configure access to GitHub Cloud and Enterprise instances.
- `languages` and `repositories`: Define language-specific settings and repository-specific overrides.

Refer to the provided `config.yml` example for detailed configuration options.

### Running the Bot

#### As a Daemon Service:

1. Ensure the `operation_mode` in `config.yml` is set to `"daemon"`.
2. Start the FastAPI server: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
3. Configure your GitHub repository to send webhook events to the service's URL.

#### With GitHub Actions:
##### Work in progress
1. Ensure the `operation_mode` in `config.yml` is set to `"github_action"`.
2. Add a `.github/workflows/code_review.yml` workflow file to your repository, configuring it to run the bot as described in the [GitHub Actions Integration](#github-actions-integration) section.

## GitHub Actions Integration

To use the Code Review Bot with GitHub Actions, create a workflow file in your repository like so:

```yaml
name: Code Review Bot

on: [pull_request]

jobs:
  code_review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Code Review Bot
        run: python actions/action_main.py ${{ github.workspace }} ${{ github.repository }} ${{ github.event.pull_request.number }} ${{ secrets.GITHUB_TOKEN }}
