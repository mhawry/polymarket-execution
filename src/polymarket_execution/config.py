"""
Configuration management for Polymarket trading.
"""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


class PolymarketConfig:
    """Configuration class for Polymarket trading parameters."""

    # Supported signature types
    VALID_SIGNATURE_TYPES = {1, 2}

    # Chain IDs
    POLYGON_MAINNET = 137
    POLYGON_TESTNET = 80001

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        # Core connection settings
        self.host = os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com")
        self.chain_id = int(os.getenv("POLYMARKET_CHAIN_ID", str(self.POLYGON_MAINNET)))

        # Authentication settings
        self.private_key = self._get_private_key()
        self.proxy_address = self._get_proxy_address()
        self.signature_type = self._get_signature_type()

        # Trading limits for safety
        self.max_order_size = float(os.getenv("POLYMARKET_MAX_ORDER_SIZE", "1000.0"))

        # Timeouts and retries
        self.connection_timeout = int(os.getenv("POLYMARKET_CONNECTION_TIMEOUT", "30"))
        self.request_timeout = int(os.getenv("POLYMARKET_REQUEST_TIMEOUT", "10"))
        self.max_retries = int(os.getenv("POLYMARKET_MAX_RETRIES", "3"))

    def _get_private_key(self) -> Optional[str]:
        """Get and validate private key from environment."""
        private_key = os.getenv("POLYMARKET_PRIVATE_KEY")

        if private_key and not self._is_valid_private_key(private_key):
            logger.warning("Private key format appears invalid")

        return private_key

    def _get_proxy_address(self) -> Optional[str]:
        """Get and validate proxy address from environment."""
        proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

        if proxy_address and not self._is_valid_ethereum_address(proxy_address):
            logger.warning("Proxy address format appears invalid")

        return proxy_address

    def _get_signature_type(self) -> int:
        """Get and validate signature type from environment."""
        try:
            sig_type = int(os.getenv("POLYMARKET_SIGNATURE_TYPE", "1"))

            if sig_type not in self.VALID_SIGNATURE_TYPES:
                logger.warning(f"Invalid signature type {sig_type}, using default 1")
                return 1

            return sig_type
        except ValueError:
            logger.warning("Invalid signature type format, using default 1")
            return 1

    def _is_valid_private_key(self, private_key: str) -> bool:
        """Validate private key format (basic check)."""
        if not private_key:
            return False

        # Remove 0x prefix if present
        clean_key = private_key.replace("0x", "")

        # Should be 64 hex characters
        return len(clean_key) == 64 and bool(re.match(r"^[0-9a-fA-F]+$", clean_key))

    def _is_valid_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if not address:
            return False

        # Remove 0x prefix if present
        clean_address = address.replace("0x", "")

        # Should be 40 hex characters
        return len(clean_address) == 40 and bool(
            re.match(r"^[0-9a-fA-F]+$", clean_address)
        )

    def validate(self) -> bool:
        """
        Validate that all required configuration is present and valid.

        Returns:
            bool: True if all required config is present, False otherwise
        """
        errors = []
        warnings = []

        # Check required fields
        if not self.private_key:
            errors.append("POLYMARKET_PRIVATE_KEY is required")
        elif not self._is_valid_private_key(self.private_key):
            errors.append("POLYMARKET_PRIVATE_KEY has invalid format")

        if not self.proxy_address:
            errors.append("POLYMARKET_PROXY_ADDRESS is required")
        elif not self._is_valid_ethereum_address(self.proxy_address):
            errors.append("POLYMARKET_PROXY_ADDRESS has invalid format")

        # Check optional but important fields
        if self.chain_id not in {self.POLYGON_MAINNET, self.POLYGON_TESTNET}:
            warnings.append(f"Unusual chain ID: {self.chain_id}")

        if self.max_order_size <= 0:
            errors.append("POLYMARKET_MAX_ORDER_SIZE must be positive")

        # Log warnings
        for warning in warnings:
            logger.warning(warning)

        # Handle errors
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            self._print_config_help()
            return False

        logger.info("Configuration validation successful")
        return True

    def _print_config_help(self) -> None:
        """Print configuration help message."""
        print("\nConfiguration Help:")
        print("Please ensure your .env file contains:")

        print("POLYMARKET_PRIVATE_KEY=your_wallet_private_key")
        print("POLYMARKET_PROXY_ADDRESS=your_polymarket_proxy_address")
        print("POLYMARKET_SIGNATURE_TYPE=1  # Optional, defaults to 1")

        print("\nOptional safety settings:")
        print("POLYMARKET_MAX_ORDER_SIZE=1000.0  # Maximum order size")
        print("POLYMARKET_CONNECTION_TIMEOUT=30  # Connection timeout in seconds")

    def get_trading_limits(self) -> dict:
        """Get trading limits for validation."""
        return {
            "max_order_size": self.max_order_size,
            "min_price": 0.01,  # Minimum meaningful price
            "min_order_size": 0.1,  # Minimum meaningful order size
        }
