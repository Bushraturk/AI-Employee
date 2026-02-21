"""
LinkedIn Watcher Module

Monitors LinkedIn for new messages, mentions, and relevant posts.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import frontmatter
import uuid
import requests

from watchers.base_watcher import BaseWatcher, WatcherStatus
from watchers.auth.linkedin_auth import LinkedInAuth

logger = logging.getLogger(__name__)


class LinkedInWatcher(BaseWatcher):
    """LinkedIn watcher - monitors messages, mentions, and posts"""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """
        Initialize LinkedIn watcher

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - poll_interval_seconds: How often to check for new content (default: 60)
                - monitor_messages: Monitor direct messages (default: True)
                - monitor_mentions: Monitor mentions and tags (default: True)
                - monitor_feed: Monitor relevant feed posts (default: False)
                - keywords: List of keywords to monitor in feed (default: [])
        """
        super().__init__(
            watcher_id='linkedin',
            watcher_type='linkedin',
            config=config
        )

        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / 'Inbox'
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.poll_interval = config.get('poll_interval_seconds', 60)
        self.monitor_messages = config.get('monitor_messages', True)
        self.monitor_mentions = config.get('monitor_mentions', True)
        self.monitor_feed = config.get('monitor_feed', False)
        self.keywords = config.get('keywords', [])

        # Authentication
        self.auth = LinkedInAuth()
        self.api_base_url = 'https://api.linkedin.com/v2'

        # State
        self.processed_item_ids = set()
        self.last_check_time = None

    def start(self) -> None:
        """Start monitoring LinkedIn"""
        logger.info("Starting LinkedIn watcher...")

        # Authenticate
        if not self.auth.authenticate():
            raise RuntimeError("LinkedIn authentication failed")

        # Verify authentication
        if not self.auth.verify_authentication():
            raise RuntimeError("LinkedIn authentication verification failed")

        self.status = WatcherStatus.RUNNING
        self.last_check_time = datetime.now()
        logger.info("LinkedIn watcher started successfully")

    def stop(self) -> None:
        """Stop monitoring LinkedIn"""
        logger.info("Stopping LinkedIn watcher...")
        self.status = WatcherStatus.STOPPED
        logger.info("LinkedIn watcher stopped")

    def get_new_tasks(self) -> List[Dict[str, Any]]:
        """
        Get new LinkedIn content and convert to tasks

        Returns:
            List of task information dictionaries
        """
        if self.status != WatcherStatus.RUNNING:
            return []

        try:
            tasks = []

            # Monitor messages
            if self.monitor_messages:
                messages = self._fetch_new_messages()
                for msg_data in messages:
                    task_info = self._content_to_task(msg_data, 'message')
                    if task_info:
                        tasks.append(task_info)

            # Monitor mentions
            if self.monitor_mentions:
                mentions = self._fetch_mentions()
                for mention_data in mentions:
                    task_info = self._content_to_task(mention_data, 'mention')
                    if task_info:
                        tasks.append(task_info)

            # Monitor feed (if enabled)
            if self.monitor_feed and self.keywords:
                feed_posts = self._fetch_relevant_feed_posts()
                for post_data in feed_posts:
                    task_info = self._content_to_task(post_data, 'feed_post')
                    if task_info:
                        tasks.append(task_info)

            self._update_last_check()
            self._reset_error_count()
            self.last_check_time = datetime.now()

            return tasks

        except Exception as e:
            logger.error(f"Error getting new tasks from LinkedIn: {e}")
            self._increment_error_count()
            if self.error_count >= 5:
                self.status = WatcherStatus.ERROR
            return []

    def mark_processed(self, task_id: str) -> None:
        """
        Mark LinkedIn content as processed

        Args:
            task_id: Task ID
        """
        self.processed_item_ids.add(task_id)

    def _fetch_new_messages(self) -> List[Dict[str, Any]]:
        """
        Fetch new direct messages from LinkedIn

        Returns:
            List of message data dictionaries
        """
        try:
            headers = self.auth.get_headers()
            if not headers:
                logger.error("No valid authentication headers")
                return []

            # Get conversations
            # Note: LinkedIn Messaging API requires additional permissions
            # This is a simplified implementation
            url = f'{self.api_base_url}/me/conversations'
            params = {
                'q': 'actor',
                'count': 10
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 401:
                logger.error("LinkedIn authentication expired")
                self.status = WatcherStatus.ERROR
                return []

            if response.status_code != 200:
                logger.warning(f"LinkedIn API returned status {response.status_code}")
                return []

            data = response.json()
            messages = []

            # Process conversations
            for conversation in data.get('elements', []):
                conversation_id = conversation.get('entityUrn', '')

                # Skip if already processed
                if conversation_id in self.processed_item_ids:
                    continue

                # Get conversation details
                last_activity = conversation.get('lastActivityAt', 0)

                # Only process recent conversations (since last check)
                if self.last_check_time:
                    last_check_timestamp = int(self.last_check_time.timestamp() * 1000)
                    if last_activity <= last_check_timestamp:
                        continue

                # Extract message data
                participants = conversation.get('participants', [])
                sender_name = "Unknown"
                if participants:
                    sender_name = participants[0].get('name', 'Unknown')

                messages.append({
                    'item_id': conversation_id,
                    'type': 'message',
                    'sender_name': sender_name,
                    'content': conversation.get('lastMessage', {}).get('text', ''),
                    'timestamp': datetime.fromtimestamp(last_activity / 1000).isoformat(),
                    'url': f"https://www.linkedin.com/messaging/thread/{conversation_id}"
                })

                self.processed_item_ids.add(conversation_id)

            return messages

        except Exception as e:
            logger.error(f"Error fetching LinkedIn messages: {e}")
            return []

    def _fetch_mentions(self) -> List[Dict[str, Any]]:
        """
        Fetch mentions and tags

        Returns:
            List of mention data dictionaries
        """
        try:
            headers = self.auth.get_headers()
            if not headers:
                return []

            # Get social actions (mentions, tags, comments)
            url = f'{self.api_base_url}/socialActions'
            params = {
                'q': 'actor',
                'count': 20
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                logger.warning(f"LinkedIn mentions API returned status {response.status_code}")
                return []

            data = response.json()
            mentions = []

            # Process social actions
            for action in data.get('elements', []):
                action_id = action.get('id', '')

                # Skip if already processed
                if action_id in self.processed_item_ids:
                    continue

                # Check if it's a mention or tag
                action_type = action.get('verb', '')
                if action_type not in ['MENTION', 'TAG', 'COMMENT']:
                    continue

                # Extract mention data
                actor = action.get('actor', {})
                actor_name = actor.get('name', 'Unknown')

                content = action.get('object', {}).get('text', '')
                created_time = action.get('created', {}).get('time', 0)

                mentions.append({
                    'item_id': action_id,
                    'type': 'mention',
                    'sender_name': actor_name,
                    'content': content,
                    'action_type': action_type,
                    'timestamp': datetime.fromtimestamp(created_time / 1000).isoformat(),
                    'url': action.get('object', {}).get('url', '')
                })

                self.processed_item_ids.add(action_id)

            return mentions

        except Exception as e:
            logger.error(f"Error fetching LinkedIn mentions: {e}")
            return []

    def _fetch_relevant_feed_posts(self) -> List[Dict[str, Any]]:
        """
        Fetch relevant posts from LinkedIn feed based on keywords

        Returns:
            List of post data dictionaries
        """
        try:
            headers = self.auth.get_headers()
            if not headers:
                return []

            # Get feed posts
            url = f'{self.api_base_url}/feed'
            params = {
                'q': 'actor',
                'count': 20
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                logger.warning(f"LinkedIn feed API returned status {response.status_code}")
                return []

            data = response.json()
            relevant_posts = []

            # Process feed posts
            for post in data.get('elements', []):
                post_id = post.get('id', '')

                # Skip if already processed
                if post_id in self.processed_item_ids:
                    continue

                # Extract post content
                content = post.get('specificContent', {}).get('com.linkedin.ugc.ShareContent', {})
                text = content.get('shareCommentary', {}).get('text', '')

                # Check if post contains any keywords
                if not any(keyword.lower() in text.lower() for keyword in self.keywords):
                    continue

                # Extract post data
                author = post.get('author', '')
                created_time = post.get('created', {}).get('time', 0)

                relevant_posts.append({
                    'item_id': post_id,
                    'type': 'feed_post',
                    'sender_name': author,
                    'content': text,
                    'timestamp': datetime.fromtimestamp(created_time / 1000).isoformat(),
                    'url': f"https://www.linkedin.com/feed/update/{post_id}"
                })

                self.processed_item_ids.add(post_id)

            return relevant_posts

        except Exception as e:
            logger.error(f"Error fetching LinkedIn feed posts: {e}")
            return []

    def _content_to_task(self, content_data: Dict[str, Any], content_type: str) -> Optional[Dict[str, Any]]:
        """
        Convert LinkedIn content to task format

        Args:
            content_data: Content data dictionary
            content_type: Type of content (message, mention, feed_post)

        Returns:
            Task information dictionary or None if conversion fails
        """
        try:
            # Create task file
            task_id = str(uuid.uuid4())
            task_file = self.inbox_path / f"{task_id}.md"

            # Create task metadata
            metadata = {
                'task_id': task_id,
                'title': f"LinkedIn {content_type.replace('_', ' ').title()}: {content_data['content'][:50]}...",
                'priority': 'P2',  # Default, will be classified by agent skill
                'status': 'inbox',
                'channel': 'linkedin',
                'channel_metadata': {
                    'sender_name': content_data['sender_name'],
                    'item_id': content_data['item_id'],
                    'content_type': content_type,
                    'timestamp': content_data['timestamp'],
                    'url': content_data.get('url', '')
                },
                'created_at': datetime.now().isoformat(),
                'category': content_type
            }

            # Create task content
            content = f"# LinkedIn {content_type.replace('_', ' ').title()} from {content_data['sender_name']}\n\n"
            content += f"**Type**: {content_type}\n\n"
            content += f"**Timestamp**: {content_data['timestamp']}\n\n"

            if content_data.get('url'):
                content += f"**URL**: {content_data['url']}\n\n"

            content += f"**Content**:\n\n{content_data['content']}\n\n"
            content += f"---\n\n"
            content += f"**Action Required**: Classify and process this LinkedIn {content_type}\n"

            # Write task file
            post = frontmatter.Post(content, **metadata)
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            logger.info(f"Created task from LinkedIn {content_type}: {content_data['sender_name']}")

            return {
                'file_path': str(task_file),
                'task_id': task_id,
                'detected_at': datetime.now().isoformat(),
                'channel': 'linkedin',
                'item_id': content_data['item_id']
            }

        except Exception as e:
            logger.error(f"Error converting LinkedIn content to task: {e}")
            return None

    def _handle_rate_limit(self, retry_after: int = 60):
        """
        Handle LinkedIn API rate limit

        Args:
            retry_after: Seconds to wait before retry
        """
        logger.warning(f"LinkedIn API rate limit hit, waiting {retry_after} seconds...")
        time.sleep(retry_after)
