"""Tests for the PolymarketConfig class."""

import os
from unittest.mock import patch

from polymarket_execution.config import PolymarketConfig


class TestPolymarketConfig:
    """Test suite for PolymarketConfig."""

    def test_init_default_values(self):
        """Test that default values are set correctly."""
        config = PolymarketConfig()

        assert config.host == "https://clob.polymarket.com"
        assert config.chain_id == 137
        assert config.signature_type == 1

    @patch.dict(
        os.environ,
        {
            "POLYMARKET_PRIVATE_KEY": "test_key",
            "POLYMARKET_PROXY_ADDRESS": "test_address",
            "POLYMARKET_SIGNATURE_TYPE": "2",
        },
    )
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        config = PolymarketConfig()

        assert config.private_key == "test_key"
        assert config.proxy_address == "test_address"
        assert config.signature_type == 2

    @patch.dict(
        os.environ,
        {
            "POLYMARKET_PRIVATE_KEY": "0x" + "a" * 64,
            "POLYMARKET_PROXY_ADDRESS": "0x" + "b" * 40,
        },
    )
    def test_validate_success(self):
        """Test successful validation."""
        config = PolymarketConfig()

        assert config.validate()

    @patch.dict(os.environ, {}, clear=True)
    def test_signature_type_default(self):
        """Test that signature type defaults to 1 when not set."""
        config = PolymarketConfig()

        assert config.signature_type == 1

    @patch.dict(os.environ, {"POLYMARKET_SIGNATURE_TYPE": "invalid"})
    def test_signature_type_invalid(self):
        """Test handling of invalid signature type."""
        config = PolymarketConfig()
        # Should default to 1 when invalid value provided
        assert config.signature_type == 1

    @patch.dict(
        os.environ,
        {
            "POLYMARKET_PRIVATE_KEY": "0x" + "a" * 64,
            "POLYMARKET_PROXY_ADDRESS": "0x" + "b" * 40,
            "POLYMARKET_MAX_ORDER_SIZE": "500.0",
        },
    )
    def test_trading_limits(self):
        """Test trading limits configuration."""
        config = PolymarketConfig()
        limits = config.get_trading_limits()

        assert limits["max_order_size"] == 500.0

        assert limits["min_price"] == 0.01
        assert limits["min_order_size"] == 0.1

    @patch.dict(
        os.environ,
        {
            "POLYMARKET_PRIVATE_KEY": "invalid_key",
            "POLYMARKET_PROXY_ADDRESS": "0x" + "b" * 40,
        },
    )
    def test_validate_invalid_private_key(self):
        """Test validation with invalid private key."""
        config = PolymarketConfig()
        assert not config.validate()

    @patch.dict(
        os.environ,
        {
            "POLYMARKET_PRIVATE_KEY": "0x" + "a" * 64,
            "POLYMARKET_PROXY_ADDRESS": "invalid_address",
        },
    )
    def test_validate_invalid_proxy_address(self):
        """Test validation with invalid proxy address."""
        config = PolymarketConfig()
        assert not config.validate()
