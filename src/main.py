"""Main entry point for AI Employee system."""

import sys
import os
import logging
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


def load_configuration() -> dict:
    """Load configuration from environment variables.

    Returns:
        Configuration dictionary
    """
    # Load .env file
    load_dotenv()

    # Get required configuration
    vault_path = os.getenv('VAULT_PATH')
    if not vault_path:
        raise ValueError("VAULT_PATH not set in environment")

    config = {
        'vault_path': vault_path,
        'claude_code_path': os.getenv('CLAUDE_CODE_PATH', 'claude'),
        'task_timeout': int(os.getenv('TASK_TIMEOUT', '60')),
        'max_retries': 3,
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
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
        logger.info("=" * 60)
        logger.info("AI Employee System - Bronze Phase")
        logger.info("=" * 60)

        # Load configuration
        logger.info("Loading configuration...")
        config = load_configuration()

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
