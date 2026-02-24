"""Main entry point for AI Employee system."""

import sys
import os
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from orchestrator import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='AI Employee System - Autonomous task processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run in Bronze/Silver mode
  python main.py --gold-tier        # Run in Gold Tier mode (autonomous)
  python main.py --gold-tier --verbose  # Gold Tier with verbose logging
        """
    )

    parser.add_argument(
        '--gold-tier',
        action='store_true',
        help='Enable Gold Tier features (Odoo sync, social media, autonomous workflows)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    parser.add_argument(
        '--vault',
        type=str,
        help='Override vault path from environment'
    )

    return parser.parse_args()


def load_configuration(args) -> dict:
    """Load configuration from environment variables and arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Configuration dictionary
    """
    # Load .env file
    load_dotenv()

    # Get required configuration
    vault_path = args.vault or os.getenv('VAULT_PATH')
    if not vault_path:
        raise ValueError("VAULT_PATH not set in environment or --vault argument")

    config = {
        'vault_path': vault_path,
        'claude_code_path': os.getenv('CLAUDE_CODE_PATH', 'claude'),
        'task_timeout': int(os.getenv('TASK_TIMEOUT', '60')),
        'max_retries': 3,
        'log_level': 'DEBUG' if args.verbose else os.getenv('LOG_LEVEL', 'INFO'),
        'gold_tier': args.gold_tier
    }

    return config


def validate_configuration(config: dict) -> bool:
    """Validate configuration before starting.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, False otherwise
    """
    # Check vault path exists
    vault_path = Path(config['vault_path'])
    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        return False

    # Check vault path is a directory
    if not vault_path.is_dir():
        logger.error(f"Vault path is not a directory: {vault_path}")
        return False

    # Check write permissions
    if not os.access(vault_path, os.W_OK):
        logger.error(f"No write permission for vault path: {vault_path}")
        return False

    logger.info("Configuration validated successfully")
    return True


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Configure logging based on arguments
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Reconfigure if already configured
        )

        # Display banner
        tier_name = "Gold Tier (Autonomous)" if args.gold_tier else "Bronze/Silver Tier"
        logger.info("=" * 60)
        logger.info(f"AI Employee System - {tier_name}")
        logger.info("=" * 60)

        if args.gold_tier:
            logger.info("Gold Tier Features Enabled:")
            logger.info("  - Odoo Integration (bidirectional sync)")
            logger.info("  - Social Media Management (multi-platform)")
            logger.info("  - Weekly Business Intelligence Reports")
            logger.info("  - Autonomous Multi-Step Workflows (Ralph Wiggum)")
            logger.info("  - MCP Server Orchestration")
            logger.info("  - Advanced Error Recovery")
            logger.info("=" * 60)

        # Load configuration
        logger.info("Loading configuration...")
        config = load_configuration(args)

        # Validate configuration
        if not validate_configuration(config):
            logger.error("Configuration validation failed")
            sys.exit(1)

        # Create and start orchestrator
        orchestrator = Orchestrator(config)
        orchestrator.start()

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
