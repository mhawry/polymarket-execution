"""Tests for the CLI module."""

from unittest.mock import Mock, patch

import pytest

from polymarket_execution.cli import create_parser, main


class TestCLI:
    """Test suite for CLI functionality."""

    def test_create_parser(self):
        """Test parser creation and argument configuration."""
        parser = create_parser()

        # Test no arguments - should show help, not fail
        args = parser.parse_args([])
        assert args.command is None

        # Test valid trade command
        args = parser.parse_args(
            ["trade", "--token-id", "123", "--price", "0.6", "--size", "10.0"]
        )

        assert args.token_id == "123"
        assert args.price == 0.6
        assert args.size == 10.0
        assert args.dry_run is False
        assert args.command == "trade"

        # Test with verbose flag
        args = parser.parse_args(["-v"])
        assert args.verbose is True

    def test_create_parser_with_dry_run(self):
        """Test parser with dry-run flag."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "trade",
                "--token-id",
                "123",
                "--price",
                "0.6",
                "--size",
                "10.0",
                "--dry-run",
            ]
        )

        assert args.dry_run is True

    @patch("polymarket_execution.cli.load_dotenv")
    @patch("polymarket_execution.cli.PolymarketConfig")
    @patch("polymarket_execution.cli.PolymarketTrader")
    @patch(
        "sys.argv",
        [
            "polymarket-execute",
            "trade",
            "--token-id",
            "123",
            "--price",
            "0.6",
            "--size",
            "10.0",
            "--dry-run",
        ],
    )
    def test_main_dry_run(self, mock_trader, mock_config, _):
        """Test main function with dry-run mode."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.validate.return_value = True
        mock_config_instance.get_trading_limits.return_value = {
            "max_order_size": 1000.0,
            "min_price": 0.01,
            "min_order_size": 0.1,
        }
        mock_config.return_value = mock_config_instance

        mock_trader_instance = Mock()
        mock_trader_instance._validate_order_params.return_value = None
        mock_trader.return_value = mock_trader_instance

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        # Verify dry-run output
        mock_print.assert_any_call("DRY RUN MODE - No actual trades will be placed")
        mock_print.assert_any_call("Would place BUY order:")

    @patch("polymarket_execution.cli.load_dotenv")
    @patch("polymarket_execution.cli.PolymarketConfig")
    @patch(
        "sys.argv",
        [
            "polymarket-execute",
            "trade",
            "--token-id",
            "123",
            "--price",
            "0.6",
            "--size",
            "10.0",
        ],
    )
    def test_main_config_validation_failure(self, mock_config, _):
        """Test main function with config validation failure."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.validate.return_value = False
        mock_config.return_value = mock_config_instance

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("polymarket_execution.cli.load_dotenv")
    @patch("polymarket_execution.cli.PolymarketConfig")
    @patch("polymarket_execution.cli.PolymarketTrader")
    @patch(
        "sys.argv",
        [
            "polymarket-execute",
            "trade",
            "--token-id",
            "123",
            "--price",
            "0.6",
            "--size",
            "10.0",
        ],
    )
    def test_main_client_init_failure(self, mock_trader, mock_config, _):
        """Test main function with client initialization failure."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.validate.return_value = True
        mock_config.return_value = mock_config_instance

        mock_trader_instance = Mock()
        mock_trader_instance.initialize_client.return_value = False
        mock_trader.return_value = mock_trader_instance

        with pytest.raises(SystemExit) as exc_info:
            with patch("builtins.print") as mock_print:
                main()

        assert exc_info.value.code == 1
        mock_print.assert_called_with("Failed to initialize trading client")

    @patch("polymarket_execution.cli.load_dotenv")
    @patch("polymarket_execution.cli.PolymarketConfig")
    @patch("polymarket_execution.cli.PolymarketTrader")
    @patch(
        "sys.argv",
        [
            "polymarket-execute",
            "trade",
            "--token-id",
            "123",
            "--price",
            "0.6",
            "--size",
            "10.0",
        ],
    )
    def test_main_successful_trade(self, mock_trader, mock_config, _):
        """Test main function with successful trade."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.validate.return_value = True
        mock_config.return_value = mock_config_instance

        mock_trader_instance = Mock()
        mock_trader_instance.initialize_client.return_value = True
        mock_trader_instance.place_buy_order.return_value = True
        mock_trader.return_value = mock_trader_instance

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_print.assert_called_with("Trade executed successfully!")

    @patch("polymarket_execution.cli.load_dotenv")
    @patch("polymarket_execution.cli.PolymarketConfig")
    @patch("polymarket_execution.cli.PolymarketTrader")
    @patch(
        "sys.argv",
        [
            "polymarket-execute",
            "trade",
            "--token-id",
            "123",
            "--price",
            "0.6",
            "--size",
            "10.0",
        ],
    )
    def test_main_failed_trade(self, mock_trader, mock_config, _):
        """Test main function with failed trade."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.validate.return_value = True
        mock_config.return_value = mock_config_instance

        mock_trader_instance = Mock()
        mock_trader_instance.initialize_client.return_value = True
        mock_trader_instance.place_buy_order.return_value = False
        mock_trader.return_value = mock_trader_instance

        with pytest.raises(SystemExit) as exc_info:
            with patch("builtins.print") as mock_print:
                main()

        assert exc_info.value.code == 1
        mock_print.assert_called_with("Failed to execute trade")
