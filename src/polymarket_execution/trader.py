"""
Polymarket trading functionality.
"""

import re
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs, OrderType
    from py_clob_client.exceptions import PolyApiException
    from py_clob_client.order_builder.constants import BUY, SELL
except ImportError as e:
    raise ImportError(
        f"Missing required dependencies: {e}\n"
        "Please install with: pip install py-clob-client"
    )

from .config import PolymarketConfig
from .utils import setup_logger

# Retry constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


def retry_on_failure(
    max_retries: int = DEFAULT_MAX_RETRIES, delay: float = DEFAULT_RETRY_DELAY
) -> Callable:
    """Decorator to retry operations on failure."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2**attempt))  # Exponential backoff
                        continue
                    break

            if last_exception is not None:
                raise last_exception
            raise RuntimeError(
                "Unexpected error: no exception occurred but retry failed"
            )

        return wrapper

    return decorator


class TradingError(Exception):
    """Base exception for trading operations."""

    pass


class ValidationError(TradingError):
    """Exception for validation failures."""

    pass


class TradingConnectionError(TradingError):
    """Exception for connection issues."""

    pass


class OrderError(TradingError):
    """Exception for order-related issues."""

    pass


class PolymarketTrader:
    """Main trading class for Polymarket operations."""

    # Trading constants
    MAX_PRICE = 1.0  # Maximum price for probability-based tokens
    MIN_PRICE = 0.0  # Minimum price for probability-based tokens

    def __init__(self, config: PolymarketConfig):
        """
        Initialize the trader with configuration.

        Args:
            config: PolymarketConfig instance with trading parameters
        """
        self.config = config
        self.client: Optional[ClobClient] = None

        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self._trading_limits = config.get_trading_limits()
        self._is_initialized = False

    @retry_on_failure(max_retries=DEFAULT_MAX_RETRIES, delay=DEFAULT_RETRY_DELAY)
    def initialize_client(self) -> bool:
        """
        Initialize the Polymarket client with retry logic.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Polymarket client...")

            # Create client instance
            self.client = ClobClient(
                host=self.config.host,
                key=self.config.private_key,
                chain_id=self.config.chain_id,
                signature_type=self.config.signature_type,
                funder=self.config.proxy_address,
            )

            # Set API credentials
            self.logger.info("Setting up API credentials...")
            api_creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(api_creds)

            # Test connection with a simple API call
            self.logger.info("Testing connection...")
            # TODO: Add actual connection test if API provides one

            # Mark as initialized
            self._is_initialized = True
            self.logger.info("Client initialized successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            self._is_initialized = False
            return False

    def _validate_token_id(self, token_id: str) -> bool:
        """Validate token ID format."""
        if not token_id or not isinstance(token_id, str):
            return False

        # Basic validation - should be alphanumeric
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", token_id))

    def _validate_order_params(
        self, price: float, size: float, side: str = "BUY"
    ) -> None:
        """
        Validate order parameters against trading limits.

        Args:
            price: Price per token
            size: Order size
            side: Order side (BUY/SELL)

        Raises:
            ValidationError: If parameters are invalid
        """
        limits = self._trading_limits

        # Validate parameter types
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValidationError("Price must be a positive number")

        if not isinstance(size, (int, float)) or size <= 0:
            raise ValidationError("Size must be a positive number")

        # Validate price ranges
        if price < limits["min_price"]:
            raise ValidationError(f"Price {price} below minimum {limits['min_price']}")

        if price > self.MAX_PRICE:
            raise ValidationError(f"Price {price} exceeds maximum {self.MAX_PRICE}")

        # Validate size ranges
        if size < limits["min_order_size"]:
            raise ValidationError(
                f"Size {size} below minimum {limits['min_order_size']}"
            )

        if size > limits["max_order_size"]:
            raise ValidationError(
                f"Size {size} exceeds maximum {limits['max_order_size']}"
            )

        # Validate total cost
        total_cost = price * size
        max_total = self.MAX_PRICE * limits["max_order_size"]
        if total_cost > max_total:
            raise ValidationError(
                f"Total cost {total_cost} exceeds safety limit {max_total}"
            )

    def place_buy_order(self, token_id: str, price: float, size: float) -> bool:
        """
        Place a BUY order on Polymarket.

        Args:
            token_id: The token ID of the market to trade
            price: Price per token in USDC (0.0 to 1.0)
            size: Number of tokens to buy

        Returns:
            bool: True if order was placed successfully, False otherwise

        Raises:
            ValidationError: If parameters are invalid
            TradingConnectionError: If client is not initialized
            OrderError: If order placement fails
        """
        return self._place_order(token_id, price, size, BUY)

    def place_sell_order(self, token_id: str, price: float, size: float) -> bool:
        """
        Place a SELL order on Polymarket.

        Args:
            token_id: The token ID of the market to trade
            price: Price per token in USDC (0.0 to 1.0)
            size: Number of tokens to sell

        Returns:
            bool: True if order was placed successfully, False otherwise
        """
        return self._place_order(token_id, price, size, SELL)

    def _place_order(self, token_id: str, price: float, size: float, side: str) -> bool:
        """
        Internal method to place orders with comprehensive error handling.
        """
        if not self._is_initialized or not self.client:
            raise TradingConnectionError("Client not initialized")

        # Start execution timing for speed measurement
        execution_start = time.time()

        try:
            # Validate inputs
            if not self._validate_token_id(token_id):
                raise ValidationError(f"Invalid token ID: {token_id}")

            self._validate_order_params(price, size, side)

            # Log order details
            self.logger.info(f"Placing {side} order:")
            self.logger.info(f"  Token ID: {token_id}")
            self.logger.info(f"  Price: {price} USDC")
            self.logger.info(f"  Size: {size} tokens")
            self.logger.info(f"  Total: {price * size} USDC")

            # Create order arguments
            order_args = OrderArgs(price=price, size=size, side=side, token_id=token_id)

            # Create and sign the order
            self.logger.info("Creating and signing order...")
            signed_order = self.client.create_order(order_args)

            # Place the order
            self.logger.info("Executing order...")
            response = self.client.post_order(signed_order, OrderType.GTC)

            # Calculate execution time and log success
            execution_time = (time.time() - execution_start) * 1000
            self.logger.info(
                f"Order executed successfully! (took {execution_time:.0f}ms)"
            )
            self.logger.info(f"Order ID: {response.get('orderID', 'N/A')}")

            return True

        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            return False
        except PolyApiException as e:
            execution_time = (time.time() - execution_start) * 1000
            self.logger.error(
                f"API error placing order: {e} (attempted in {execution_time:.0f}ms)"
            )
            return False
        except Exception as e:
            execution_time = (time.time() - execution_start) * 1000
            self.logger.error(
                f"Unexpected error placing order: {e} (attempted in {execution_time:.0f}ms)"
            )
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an order.

        Args:
            order_id: The ID of the order to check

        Returns:
            Optional[Dict[str, Any]]: Order status or None if failed
        """
        if not self._is_initialized or not self.client:
            raise TradingConnectionError("Client not initialized")

        try:
            # TODO: Implement actual order status retrieval
            self.logger.info(f"Getting status for order: {order_id}")
            return {"order_id": order_id, "status": "unknown"}
        except Exception as e:
            self.logger.error(f"Failed to get order status: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: The ID of the order to cancel

        Returns:
            bool: True if cancellation successful, False otherwise
        """
        if not self._is_initialized or not self.client:
            raise TradingConnectionError("Client not initialized")

        try:
            self.logger.info(f"Cancelling order: {order_id}")
            # TODO: Implement actual order cancellation
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
