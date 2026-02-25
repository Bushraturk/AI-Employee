"""Scheduler for periodic tasks using APScheduler."""

import logging
from typing import Callable, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor


logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for periodic tasks.

    Wraps APScheduler with simplified interface and job persistence.
    """

    def __init__(self, job_store_path: Optional[str] = None):
        """Initialize task scheduler.

        Args:
            job_store_path: Path to SQLite database for job persistence
        """
        # Configure job stores
        jobstores = {}
        if job_store_path:
            jobstores["default"] = SQLAlchemyJobStore(url=f"sqlite:///{job_store_path}")

        # Configure executors
        executors = {
            "default": ThreadPoolExecutor(max_workers=10),
        }

        # Configure job defaults
        job_defaults = {
            "coalesce": True,  # Combine missed runs
            "max_instances": 1,  # Only one instance per job
            "misfire_grace_time": 60,  # Allow 60 seconds grace for missed jobs
        }

        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
        )

        self._running = False
        logger.info(f"Initialized task scheduler (job_store={job_store_path or 'memory'})")

    def start(self) -> None:
        """Start the scheduler."""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Task scheduler stopped")

    def add_interval_job(
        self,
        func: Callable,
        seconds: int,
        job_id: str,
        args: tuple = None,
        kwargs: dict = None,
        start_immediately: bool = True,
    ) -> None:
        """Add a job that runs at fixed intervals.

        Args:
            func: Function to execute
            seconds: Interval in seconds
            job_id: Unique job identifier
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            start_immediately: Whether to run immediately on start
        """
        trigger = IntervalTrigger(seconds=seconds)

        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
            next_run_time=datetime.now() if start_immediately else None,
        )

        logger.info(f"Added interval job: {job_id} (every {seconds}s)")

    def add_cron_job(
        self,
        func: Callable,
        cron_expression: str,
        job_id: str,
        args: tuple = None,
        kwargs: dict = None,
    ) -> None:
        """Add a job that runs on a cron schedule.

        Args:
            func: Function to execute
            cron_expression: Cron expression (e.g., "0 9 * * *" for 9am daily)
            job_id: Unique job identifier
            args: Positional arguments for func
            kwargs: Keyword arguments for func
        """
        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )

        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )

        logger.info(f"Added cron job: {job_id} (cron={cron_expression})")

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job.

        Args:
            job_id: Job identifier
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")

    def pause_job(self, job_id: str) -> None:
        """Pause a scheduled job.

        Args:
            job_id: Job identifier
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to pause job {job_id}: {e}")

    def resume_job(self, job_id: str) -> None:
        """Resume a paused job.

        Args:
            job_id: Job identifier
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to resume job {job_id}: {e}")

    def get_jobs(self) -> list:
        """Get all scheduled jobs.

        Returns:
            List of job objects
        """
        return self.scheduler.get_jobs()

    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if running, False otherwise
        """
        return self._running
