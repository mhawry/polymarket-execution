"""Tests for the PolymarketTrader class."""

from unittest.mock import Mock, patch

import pytest

from polymarket_execution.config import PolymarketConfig
from polymarket_execution.trader import PolymarketTrader


class TestPolymarketTrader:
    """Test suite for PolymarketTrader."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=PolymarketConfig)
        config.host = "https://test.polymarket.com"
        config.private_key = "test_key"
        config.chain_id = 137
        config.signature_type = 1
        config.proxy_address = "test_proxy"
        return config

    @pytest.fixture
    def trader(self, mock_config):
        """Create a trader instance with mock config."""
        return PolymarketTrader(mock_config)

    def test_init(self, trader, mock_config):
        """Test trader initialization."""
        assert trader.config == mock_config
        assert trader.client is None
        assert trader.logger is not None

    @patch("polymarket_execution.trader.ClobClient")
    def test_initialize_client_success(self, mock_clob_client, trader):
        """Test successful client initialization."""
        # Mock the client instance
        mock_client_instance = Mock()
        mock_clob_client.return_value = mock_client_instance

        # Mock the API credentials methods
        mock_client_instance.create_or_derive_api_creds.return_value = "mock_creds"

        result = trader.initialize_client()

        assert result is True
        assert trader.client == mock_client_instance
        mock_clob_client.assert_called_once_with(
            host=trader.config.host,
            key=trader.config.private_key,
            chain_id=trader.config.chain_id,
            signature_type=trader.config.signature_type,
            funder=trader.config.proxy_address,
        )
        mock_client_instance.set_api_creds.assert_called_once_with("mock_creds")

    @patch("polymarket_execution.trader.ClobClient")
    def test_initialize_client_failure(self, mock_clob_client, trader):
        """Test client initialization failure."""
        mock_clob_client.side_effect = Exception("Connection failed")

        result = trader.initialize_client()

        assert result is False
        assert trader.client is None

    def test_place_buy_order_no_client(self, trader):
        """Test placing order without initialized client."""
        # Test expects TradingConnectionError to be raised
        with pytest.raises(Exception):  # Will raise TradingConnectionError
            trader.place_buy_order("token123", 0.5, 10.0)

    def test_place_buy_order_invalid_price(self, trader):
        """Test placing order with invalid price."""
        trader.client = Mock()  # Mock client
        trader._is_initialized = True  # Set initialized flag

        # Test price too low
        result = trader.place_buy_order("token123", 0.0, 10.0)
        assert result is False

        # Test price too high
        result = trader.place_buy_order("token123", 1.5, 10.0)
        assert result is False

    def test_place_buy_order_invalid_size(self, trader):
        """Test placing order with invalid size."""
        trader.client = Mock()  # Mock client
        trader._is_initialized = True  # Set initialized flag

        result = trader.place_buy_order("token123", 0.5, 0.0)
        assert result is False

        result = trader.place_buy_order("token123", 0.5, -1.0)
        assert result is False

    def test_place_buy_order_success(self, trader):
        """Test successful order placement."""
        with (
            patch("polymarket_execution.trader.OrderArgs") as mock_order_args,
            patch("polymarket_execution.trader.OrderType") as mock_order_type,
            patch("polymarket_execution.trader.BUY", "BUY"),
        ):

            # Setup trader
            trader._is_initialized = True
            trader.client = Mock()

            # Set up trading limits (needed for validation)
            trader._trading_limits = {
                "max_order_size": 1000.0,
                "min_price": 0.01,
                "min_order_size": 0.1,
            }

            # Mock the response
            trader.client.post_order.return_value = {"orderID": "123"}
            trader.client.create_order.return_value = Mock()

            # Set up OrderType mock
            mock_order_type.GTC = "GTC"

            # Make OrderArgs return a mock when called
            mock_order_args.return_value = Mock()

            # Call the method
            result = trader.place_buy_order("token123", 0.6, 10.0)

            # Verify
            assert result is True
            mock_order_args.assert_called_once_with(
                price=0.6, size=10.0, side="BUY", token_id="token123"
            )

    def test_place_buy_order_exception(self, trader):
        """Test order placement with exception."""
        trader.client = Mock()
        trader._is_initialized = True  # Set initialized flag
        trader.client.create_order.side_effect = Exception("Order failed")

        result = trader.place_buy_order("token123", 0.6, 10.0)

        assert result is False
