"""Category Mapper for Odoo Integration.

Maps vault categories to Odoo account IDs using Company Handbook rules.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import yaml

logger = logging.getLogger(__name__)


class CategoryMapper:
    """Maps vault transaction categories to Odoo account IDs.

    Reads mapping from Company Handbook or configuration file.
    """

    def __init__(self, vault_path: Path, config_path: Optional[Path] = None):
        """Initialize category mapper.

        Args:
            vault_path: Path to AI Employee vault
            config_path: Path to category mapping configuration
        """
        self.vault_path = vault_path
        self.config_path = config_path or Path("config/category_mapping.yaml")
        self.category_map: Dict[str, int] = {}

        # Load category mappings
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load category mappings from configuration file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.category_map = config.get('category_mappings', {})
                    logger.info(f"Loaded {len(self.category_map)} category mappings")
            except Exception as e:
                logger.error(f"Failed to load category mappings: {e}")
                self._load_default_mappings()
        else:
            logger.warning("Category mapping file not found, using defaults")
            self._load_default_mappings()

    def _load_default_mappings(self) -> None:
        """Load default category mappings."""
        # Default mappings (placeholder account IDs)
        self.category_map = {
            "Revenue - Consulting": 400001,
            "Revenue - Products": 400002,
            "Revenue - Services": 400003,
            "Expenses - General": 600001,
            "Expenses - Marketing": 600002,
            "Expenses - Software": 600003,
            "Expenses - Operations": 600004,
            "Expenses - Travel": 600005,
        }
        logger.info("Loaded default category mappings")

    def get_account_id(self, category: str) -> Optional[int]:
        """Get Odoo account ID for a category.

        Args:
            category: Category name from vault

        Returns:
            Odoo account ID or None if not found
        """
        account_id = self.category_map.get(category)

        if not account_id:
            logger.warning(f"No account mapping found for category: {category}")
            # Return default account ID
            return 600001  # Default to general expenses

        return account_id

    def get_all_categories(self) -> list:
        """Get list of all mapped categories.

        Returns:
            List of category names
        """
        return list(self.category_map.keys())

    def add_mapping(self, category: str, account_id: int) -> bool:
        """Add or update a category mapping.

        Args:
            category: Category name
            account_id: Odoo account ID

        Returns:
            True if mapping added successfully
        """
        try:
            self.category_map[category] = account_id

            # Save to configuration file
            self._save_mappings()

            logger.info(f"Added mapping: {category} -> {account_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add mapping: {e}")
            return False

    def _save_mappings(self) -> None:
        """Save category mappings to configuration file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            config = {
                'category_mappings': self.category_map
            }

            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            logger.info("Saved category mappings to configuration")

        except Exception as e:
            logger.error(f"Failed to save category mappings: {e}")

    def validate_category(self, category: str) -> bool:
        """Check if category has a valid mapping.

        Args:
            category: Category name

        Returns:
            True if category is mapped
        """
        return category in self.category_map
