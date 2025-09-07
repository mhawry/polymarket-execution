# Polymarket Execution Engine


The Polymarket Execution Engine provides a streamlined interface for placing buy and sell orders on Polymarket's CLOB (Central Limit Order Book). It features comprehensive validation, error handling, and configurable safety limits to ensure reliable trade execution.

## Features

- **Fast Order Execution**: Optimized for low-latency trading with timing metrics
- **Comprehensive Validation**: Input validation with safety limits and error handling
- **Retry Logic**: Automatic retry with exponential backoff for network failures
- **Dry Run Mode**: Test orders without actual execution
- **UTC Logging**: Precise timestamping for audit trails
- **Environment-based Configuration**: Secure credential management

## Requirements

- Python 3.12+
- A Polymarket account with API access
- Wallet private key and proxy address

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd polymarket-execution
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

For production use:
```bash
make install
```

For development:
```bash
make install-dev
```

### 4. Configuration

Create a `.env` file in the project root:

```bash
# Required settings
POLYMARKET_PRIVATE_KEY=your_wallet_private_key
POLYMARKET_PROXY_ADDRESS=your_polymarket_proxy_address

# Optional settings
POLYMARKET_SIGNATURE_TYPE=1
POLYMARKET_MAX_ORDER_SIZE=1000.0
POLYMARKET_CONNECTION_TIMEOUT=30
```

## Usage

### Basic Trading Commands

Place a buy order:
```bash
polymarket-execute trade --token-id "12345" --price 0.60 --size 10.0
```

Place a sell order:
```bash
polymarket-execute trade --token-id "12345" --price 0.65 --size 5.0 --side sell
```

Test with dry run:
```bash
polymarket-execute trade --token-id "12345" --price 0.50 --size 5.0 --dry-run
```

### Command Line Options

| Option | Description | Required |
|--------|-------------|----------|
| `--token-id` | Token ID of the market to trade | Yes |
| `--price` | Price per token in USDC (0.01 to 1.0) | Yes |
| `--size` | Number of tokens to trade | Yes |
| `--side` | Order side: `buy` or `sell` (default: buy) | No |
| `--dry-run` | Simulate trade without execution | No |

## Development

### Available Make Commands

```bash
make help          # Show all available commands
make install       # Install production dependencies
make install-dev   # Install development dependencies
make test          # Run tests with coverage
make test-cov      # Run tests with HTML coverage report
make lint          # Run all linting tools
make format        # Format code with black and isort
make type-check    # Run mypy type checking
make clean         # Clean build artifacts
make build         # Build distribution packages
make dev-check     # Run all development checks
```

### Code Quality

The project maintains high code quality standards with:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing with coverage

Run all quality checks:
```bash
make dev-check
```

### Testing

Run the test suite:
```bash
make test
```

Generate coverage report:
```bash
make test-cov
```

## Project Structure

```
polymarket-execution/
├── src/
│   └── polymarket_execution/
│       ├── __init__.py
│       ├── cli.py          # Command-line interface
│       ├── config.py       # Configuration management
│       └── trader.py       # Core trading functionality
├── tests/                  # Test suite
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Project configuration
├── Makefile              # Development commands
└── README.md             # Project documentation
```

## Safety Features

### Trading Limits

- Maximum order size: Configurable via `POLYMARKET_MAX_ORDER_SIZE`
- Price validation: Ensures prices are between 0.01 and 1.0
- Size validation: Prevents zero or negative order sizes
- Total cost limits: Validates against safety thresholds

### Error Handling

- Comprehensive input validation
- Network retry logic with exponential backoff
- Detailed error messages and logging
- Graceful failure handling

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `POLYMARKET_PRIVATE_KEY` | Wallet private key | Yes | - |
| `POLYMARKET_PROXY_ADDRESS` | Polymarket proxy address | Yes | - |
| `POLYMARKET_SIGNATURE_TYPE` | Signature type (1 or 2) | No | 1 |
| `POLYMARKET_MAX_ORDER_SIZE` | Maximum order size | No | 1000.0 |
| `POLYMARKET_HOST` | API host URL | No | https://clob.polymarket.com |
| `POLYMARKET_CHAIN_ID` | Blockchain chain ID | No | 137 |
| `POLYMARKET_CONNECTION_TIMEOUT` | Connection timeout (seconds) | No | 30 |
| `POLYMARKET_REQUEST_TIMEOUT` | Request timeout (seconds) | No | 10 |
| `POLYMARKET_MAX_RETRIES` | Maximum retry attempts | No | 3 |

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Important Disclaimers

**NOT FOR PRODUCTION USE**: This software is created for educational and demonstration purposes only.

**NO WARRANTY**: This software is provided "AS IS" without warranty of any kind, either express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement.

**FINANCIAL RISK WARNING**: Trading cryptocurrency and prediction market tokens involves substantial risk of loss. The authors and contributors of this software:
- Make no representations about the software's suitability for actual trading
- Accept no responsibility for any financial losses incurred through use of this software
- Strongly advise against using this software with real funds

**USE AT YOUR OWN RISK**: By using this software, you acknowledge that you understand the risks involved and agree that the authors bear no responsibility for any losses or damages that may result from its use.

**TESTING ONLY**: This software should only be used in test environments with test funds. Never use production private keys or real money with this software.
