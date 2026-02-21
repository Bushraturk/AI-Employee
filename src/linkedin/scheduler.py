"""
LinkedIn Post Scheduler

Schedules and manages automated LinkedIn posting at optimal times.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import pytz

from linkedin.poster import LinkedInPoster
from linkedin.post_generator import LinkedInPostGenerator

logger = logging.getLogger(__name__)


class LinkedInScheduler:
    """Schedule automated LinkedIn posting"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize LinkedIn scheduler

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - timezone: Timezone for scheduling (default: 'UTC')
                - auto_post_frequency: Posts per week (default: 2.5)
                - auto_post_enabled: Enable automatic posting (default: False)
                - post_types: List of post types to rotate (default: ['product', 'service', 'value'])
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Configuration
        self.timezone = pytz.timezone(self.config.get('timezone', 'UTC'))
        self.auto_post_frequency = self.config.get('auto_post_frequency', 2.5)
        self.auto_post_enabled = self.config.get('auto_post_enabled', False)
        self.post_types = self.config.get('post_types', ['product', 'service', 'value'])

        # Components
        self.poster = LinkedInPoster(str(vault_path), config)
        self.post_generator = LinkedInPostGenerator(str(vault_path), config)

        # Scheduler
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.scheduler.start()

        # State
        self.scheduled_jobs = {}
        self.post_type_index = 0

    def start(self) -> None:
        """Start automated posting schedule"""
        if not self.auto_post_enabled:
            logger.info("Automated posting is disabled")
            return

        logger.info("Starting LinkedIn post scheduler...")

        # Schedule recurring posts based on frequency
        self._schedule_recurring_posts()

        # Schedule pending approved posts
        self._schedule_pending_posts()

        logger.info(f"LinkedIn scheduler started with {len(self.scheduled_jobs)} jobs")

    def stop(self) -> None:
        """Stop scheduler"""
        logger.info("Stopping LinkedIn scheduler...")

        # Shutdown scheduler
        self.scheduler.shutdown(wait=False)

        logger.info("LinkedIn scheduler stopped")

    def schedule_post(self, post_id: str, scheduled_time: datetime) -> str:
        """
        Schedule a specific post

        Args:
            post_id: Post ID
            scheduled_time: When to post

        Returns:
            Job ID
        """
        # Create job
        job = self.scheduler.add_job(
            func=self._execute_post,
            trigger=DateTrigger(run_date=scheduled_time, timezone=self.timezone),
            args=[post_id],
            id=f"post_{post_id}",
            replace_existing=True
        )

        self.scheduled_jobs[post_id] = job.id

        logger.info(f"Scheduled post {post_id} for {scheduled_time}")

        return job.id

    def schedule_recurring_post_generation(self, cron_expression: str, post_type: str = None) -> str:
        """
        Schedule recurring post generation

        Args:
            cron_expression: Cron expression (e.g., "0 9 * * 1,3,5" for Mon/Wed/Fri at 9 AM)
            post_type: Type of post to generate (default: rotate through types)

        Returns:
            Job ID
        """
        # Create cron trigger
        trigger = CronTrigger.from_crontab(cron_expression, timezone=self.timezone)

        # Create job
        job = self.scheduler.add_job(
            func=self._generate_and_schedule_post,
            trigger=trigger,
            args=[post_type],
            id=f"recurring_generation_{post_type or 'rotating'}",
            replace_existing=True
        )

        logger.info(f"Scheduled recurring post generation: {cron_expression}")

        return job.id

    def cancel_scheduled_post(self, post_id: str) -> bool:
        """
        Cancel scheduled post

        Args:
            post_id: Post ID

        Returns:
            True if cancelled
        """
        job_id = self.scheduled_jobs.get(post_id)

        if not job_id:
            logger.warning(f"No scheduled job found for post: {post_id}")
            return False

        try:
            self.scheduler.remove_job(job_id)
            del self.scheduled_jobs[post_id]

            logger.info(f"Cancelled scheduled post: {post_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling scheduled post: {e}")
            return False

    def get_scheduled_posts(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled posts

        Returns:
            List of scheduled post information
        """
        scheduled = []

        for post_id, job_id in self.scheduled_jobs.items():
            try:
                job = self.scheduler.get_job(job_id)

                if job:
                    scheduled.append({
                        'post_id': post_id,
                        'job_id': job_id,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                    })

            except Exception as e:
                logger.error(f"Error getting job info: {e}")

        return scheduled

    def reschedule_post(self, post_id: str, new_time: datetime) -> bool:
        """
        Reschedule a post

        Args:
            post_id: Post ID
            new_time: New scheduled time

        Returns:
            True if rescheduled
        """
        # Cancel existing schedule
        self.cancel_scheduled_post(post_id)

        # Schedule at new time
        self.schedule_post(post_id, new_time)

        logger.info(f"Rescheduled post {post_id} to {new_time}")

        return True

    def _schedule_recurring_posts(self) -> None:
        """Schedule recurring post generation based on frequency"""
        # Calculate posts per week
        posts_per_week = self.auto_post_frequency

        # Determine posting days and times
        if posts_per_week <= 1:
            # Once per week - Monday at 9 AM
            cron_expr = "0 9 * * 1"
        elif posts_per_week <= 2:
            # Twice per week - Monday and Thursday at 9 AM
            cron_expr = "0 9 * * 1,4"
        elif posts_per_week <= 3:
            # Three times per week - Monday, Wednesday, Friday at 9 AM
            cron_expr = "0 9 * * 1,3,5"
        else:
            # More than 3 times per week - Monday through Friday at 9 AM
            cron_expr = "0 9 * * 1-5"

        # Schedule recurring generation
        self.schedule_recurring_post_generation(cron_expr)

    def _schedule_pending_posts(self) -> None:
        """Schedule all approved posts that are pending"""
        # Get approved posts
        approved_posts = self.post_generator.list_posts(status='approved')

        for post_data in approved_posts:
            post_id = post_data.get('post_id')
            scheduled_time_str = post_data.get('scheduled_time')

            if not post_id or not scheduled_time_str:
                continue

            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str)

                # Only schedule future posts
                if scheduled_time > datetime.now(self.timezone):
                    self.schedule_post(post_id, scheduled_time)

            except Exception as e:
                logger.error(f"Error scheduling post {post_id}: {e}")

    def _generate_and_schedule_post(self, post_type: str = None) -> None:
        """
        Generate a new post and schedule it

        Args:
            post_type: Type of post to generate (default: rotate)
        """
        try:
            # Determine post type
            if not post_type:
                post_type = self._get_next_post_type()

            # Create post
            result = self.poster.create_post(post_type=post_type)

            if not result:
                logger.error("Failed to create post")
                return

            post_id = result['post_id']

            logger.info(f"Generated post {post_id} (type: {post_type})")

            # If auto-approved, schedule for posting
            if result['status'] == 'approved':
                post_data = self.post_generator.get_post(post_id)
                scheduled_time_str = post_data.get('scheduled_time')

                if scheduled_time_str:
                    scheduled_time = datetime.fromisoformat(scheduled_time_str)
                    self.schedule_post(post_id, scheduled_time)

        except Exception as e:
            logger.error(f"Error generating and scheduling post: {e}")

    def _execute_post(self, post_id: str) -> None:
        """
        Execute scheduled post

        Args:
            post_id: Post ID
        """
        try:
            logger.info(f"Executing scheduled post: {post_id}")

            # Post to LinkedIn
            success = self.poster.post_to_linkedin(post_id)

            if success:
                logger.info(f"Successfully posted to LinkedIn: {post_id}")

                # Remove from scheduled jobs
                if post_id in self.scheduled_jobs:
                    del self.scheduled_jobs[post_id]

            else:
                logger.error(f"Failed to post to LinkedIn: {post_id}")

        except Exception as e:
            logger.error(f"Error executing post: {e}")

    def _get_next_post_type(self) -> str:
        """Get next post type in rotation"""
        post_type = self.post_types[self.post_type_index]

        # Increment index (with wrap-around)
        self.post_type_index = (self.post_type_index + 1) % len(self.post_types)

        return post_type

    def get_schedule_summary(self) -> Dict[str, Any]:
        """
        Get schedule summary

        Returns:
            Summary dictionary
        """
        scheduled_posts = self.get_scheduled_posts()

        summary = {
            'auto_post_enabled': self.auto_post_enabled,
            'posts_per_week': self.auto_post_frequency,
            'scheduled_posts_count': len(scheduled_posts),
            'scheduled_posts': scheduled_posts,
            'next_generation_time': None,
            'timezone': str(self.timezone)
        }

        # Get next generation time
        try:
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                if 'recurring_generation' in job.id:
                    if job.next_run_time:
                        summary['next_generation_time'] = job.next_run_time.isoformat()
                    break
        except Exception as e:
            logger.error(f"Error getting schedule summary: {e}")

        return summary

    def update_schedule(self, new_frequency: float = None, new_timezone: str = None) -> bool:
        """
        Update schedule configuration

        Args:
            new_frequency: New posts per week
            new_timezone: New timezone

        Returns:
            True if updated
        """
        try:
            # Update frequency
            if new_frequency is not None:
                self.auto_post_frequency = new_frequency

            # Update timezone
            if new_timezone:
                self.timezone = pytz.timezone(new_timezone)

            # Restart scheduler with new configuration
            self.stop()
            self.start()

            logger.info(f"Updated schedule: frequency={self.auto_post_frequency}, timezone={self.timezone}")

            return True

        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False
