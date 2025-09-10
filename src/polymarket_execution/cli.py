"""
Command-line interface for Polymarket Order Engine.
"""

import argparse
import logging
import sys
from typing import Any

from dotenv import load_dotenv

from .config import PolymarketConfig
from .trader import PolymarketTrader, TradingConnectionError, ValidationError
from .utils import setup_logger


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(
        description="Polymarket Execution Engine - High-speed order execution for prediction markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Trading Examples:
    # Place a buy order
    polymarket-execute trade --token-id "12345" --price 0.60 --size 10.0

    # Place a sell order
    polymarket-execute trade --token-id "12345" --price 0.65 --size 5.0 --side sell

    # Test configuration (dry run)
    polymarket-execute trade --token-id "12345" --price 0.50 --size 5.0 --dry-run

Environment Variables Required:
    POLYMARKET_PRIVATE_KEY    - Your wallet private key
    POLYMARKET_PROXY_ADDRESS  - Your Polymarket proxy address
    POLYMARKET_SIGNATURE_TYPE - Signature type (1 or 2)

Optional Safety Settings:
    POLYMARKET_MAX_ORDER_SIZE - Maximum order size (default: 1000.0)
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Trade command
    trade_parser = subparsers.add_parser("trade", help="Place a trade order")
    trade_parser.add_argument(
        "--token-id", required=True, help="Token ID of the market to trade"
    )
    trade_parser.add_argument(
        "--price",
        type=float,
        required=True,
        help="Price per token in USDC (0.01 to 1.0)",
    )
    trade_parser.add_argument(
        "--size", type=float, required=True, help="Number of tokens to trade"
    )
    trade_parser.add_argument(
        "--side",
        choices=["buy", "sell"],
        default="buy",
        help="Order side: buy or sell (default: buy)",
    )
    trade_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the trade without actually placing it",
    )

    return parser


def validate_trade_args(args: Any) -> bool:
    """Validate trading arguments."""
    if not args.token_id:
        print("Error: --token-id is required")
        return False

    if args.price is None:
        print("Error: --price is required")
        return False

    if args.size is None:
        print("Error: --size is required")
        return False

    if not (0.01 <= args.price <= 1.0):
        print("Error: Price must be between 0.01 and 1.0")
        return False

    if args.size <= 0:
        print("Error: Size must be positive")
        return False

    return True


def setup_logging() -> None:
    """Setup logging configuration."""
    # Get root logger and configure it using shared utility
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Use shared setup_logger but configure as root logger
    temp_logger = setup_logger("temp")

    # Transfer the handler from temp logger to root logger
    if temp_logger.handlers:
        root_logger.addHandler(temp_logger.handlers[0])
        temp_logger.handlers.clear()


def handle_trade_command(args: Any, trader: PolymarketTrader) -> bool:
    """Handle trade command execution."""
    side = getattr(args, "side", "buy")

    if args.dry_run:
        print("DRY RUN MODE - No actual trades will be placed")
        print(f"Would place {side.upper()} order:")
        print(f"  Token ID: {args.token_id}")
        print(f"  Price: {args.price} USDC")
        print(f"  Size: {args.size} tokens")
        print(f"  Total: {args.price * args.size} USDC")

        # Validate in dry run mode
        try:
            trader._validate_order_params(args.price, args.size, side.upper())
            print("Order parameters are valid")
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False

    print(f"Executing {side} trade...")

    try:
        # Execute trade based on side
        if side == "buy":
            success = trader.place_buy_order(args.token_id, args.price, args.size)
        else:
            success = trader.place_sell_order(args.token_id, args.price, args.size)

        if success:
            print("Trade executed successfully!")
            return True
        else:
            print("Failed to execute trade")
            return False

    except ValidationError as e:
        print(f"Validation error: {e}")
        return False
    except TradingConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main() -> None:
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()

    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return

    # Initialize configuration
    print("Initializing configuration...")
    config = PolymarketConfig()
    if not config.validate():
        sys.exit(1)

    # Initialize trader
    print("Initializing Polymarket trader...")
    trader = PolymarketTrader(config)

    if not trader.initialize_client():
        print("Failed to initialize trading client")
        sys.exit(1)

    # Route to appropriate command handler
    success = False

    if args.command == "trade":
        if not validate_trade_args(args):
            sys.exit(1)
        success = handle_trade_command(args, trader)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        sys.exit(1)
