"""Task Processor - Parses Markdown task files with YAML frontmatter."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging
import frontmatter

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Processes Markdown task files and extracts structured data."""

    REQUIRED_FIELDS = ['task_id', 'title', 'status', 'created_at']
    VALID_STATUSES = ['inbox', 'needs_action', 'done']
    VALID_PRIORITIES = ['P1', 'P2', 'P3']

    def parse_task_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a Markdown task file and extract structured data.

        Args:
            file_path: Path to the task file

        Returns:
            Dictionary with task data, or None if parsing fails
        """
        try:
            # Read file with frontmatter
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Extract frontmatter metadata
            metadata = post.metadata

            # Validate required fields
            missing_fields = [field for field in self.REQUIRED_FIELDS if field not in metadata]
            if missing_fields:
                logger.error(f"Missing required fields in {file_path.name}: {missing_fields}")
                return None

            # Extract and validate fields
            task_data = {
                'task_id': self._validate_task_id(metadata.get('task_id')),
                'title': self._validate_title(metadata.get('title')),
                'description': post.content.strip(),
                'priority': self._validate_priority(metadata.get('priority', 'P2')),
                'status': self._validate_status(metadata.get('status')),
                'created_at': self._validate_timestamp(metadata.get('created_at')),
                'processed_at': self._validate_timestamp(metadata.get('processed_at')) if 'processed_at' in metadata else None,
                'tags': metadata.get('tags', []),
                'file_path': str(file_path.resolve())
            }

            # Validate all fields passed
            if None in [task_data['task_id'], task_data['title'], task_data['status'], task_data['created_at']]:
                logger.error(f"Validation failed for task file: {file_path.name}")
                return None

            logger.info(f"Successfully parsed task: {task_data['task_id']} - {task_data['title']}")
            return task_data

        except Exception as e:
            logger.error(f"Error parsing task file {file_path.name}: {e}")
            return None

    def _validate_task_id(self, task_id: Any) -> Optional[str]:
        """Validate task_id is a valid UUID v4.

        Args:
            task_id: Task ID to validate

        Returns:
            Valid task_id string, or None if invalid
        """
        if not task_id:
            return None

        try:
            # Try to parse as UUID
            uuid_obj = uuid.UUID(str(task_id), version=4)
            return str(uuid_obj)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid task_id format: {task_id}")
            return None

    def _validate_title(self, title: Any) -> Optional[str]:
        """Validate title is non-empty and within length limits.

        Args:
            title: Title to validate

        Returns:
            Valid title string, or None if invalid
        """
        if not title or not isinstance(title, str):
            return None

        title = title.strip()

        if len(title) == 0:
            logger.warning("Empty title")
            return None

        if len(title) > 200:
            logger.warning(f"Title exceeds 200 characters: {len(title)}")
            return None

        if '\n' in title or '\r' in title:
            logger.warning("Title contains newlines")
            return None

        return title

    def _validate_priority(self, priority: Any) -> str:
        """Validate priority is P1, P2, or P3.

        Args:
            priority: Priority to validate

        Returns:
            Valid priority string (defaults to P2 if invalid)
        """
        if priority in self.VALID_PRIORITIES:
            return priority

        logger.warning(f"Invalid priority '{priority}', defaulting to P2")
        return 'P2'

    def _validate_status(self, status: Any) -> Optional[str]:
        """Validate status is inbox, needs_action, or done.

        Args:
            status: Status to validate

        Returns:
            Valid status string, or None if invalid
        """
        if status in self.VALID_STATUSES:
            return status

        logger.warning(f"Invalid status: {status}")
        return None

    def _validate_timestamp(self, timestamp: Any) -> Optional[str]:
        """Validate timestamp is ISO 8601 format.

        Args:
            timestamp: Timestamp to validate

        Returns:
            Valid ISO 8601 timestamp string, or None if invalid
        """
        if not timestamp:
            return None

        try:
            # Try to parse as ISO 8601
            dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))

            # Allow timestamps within 1 hour in the future (to handle clock skew)
            from datetime import timedelta
            now = datetime.now(dt.tzinfo)
            if dt > now + timedelta(hours=1):
                logger.warning(f"Timestamp is too far in the future: {timestamp}")
                return None

            return timestamp
        except (ValueError, AttributeError):
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return None
