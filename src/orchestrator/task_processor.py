"""Task Processor with APScheduler for Gold Tier.

Manages scheduled jobs with SQLite persistence and YAML-based configuration.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Task processor with APScheduler for scheduled job execution.

    Features:
    - SQLite job store for persistence across restarts
    - YAML-based schedule configuration
    - Cron and interval trigger support
    - Job execution monitoring
    - Timezone handling
    """

    def __init__(self, vault_path: Path, config_path: Optional[Path] = None,
                 timezone: str = "UTC"):
        """Initialize task processor.

        Args:
            vault_path: Path to AI Employee vault
            config_path: Path to schedules configuration file
            timezone: Timezone for scheduler (default: UTC)
        """
        self.vault_path = vault_path
        self.config_path = config_path or Path("config/schedules.yaml")
        self.timezone = timezone

        # Initialize APScheduler with SQLite job store
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=timezone
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )

        # Job registry for dynamic job management
        self.job_registry: Dict[str, Callable] = {}

    def _on_job_executed(self, event) -> None:
        """Handle job execution event."""
        logger.info(f"Job {event.job_id} executed successfully")

    def _on_job_error(self, event) -> None:
        """Handle job error event."""
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")

    def register_job(self, job_id: str, job_func: Callable) -> None:
        """Register a job function.

        Args:
            job_id: Unique job identifier
            job_func: Function to execute
        """
        self.job_registry[job_id] = job_func
        logger.info(f"Registered job: {job_id}")

    def load_schedules(self) -> bool:
        """Load schedules from YAML configuration file.

        Returns:
            True if schedules loaded successfully
        """
        if not self.config_path.exists():
            logger.warning(f"Schedule configuration not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'schedules' not in config:
                logger.warning("No schedules found in configuration")
                return False

            schedules = config['schedules']

            for schedule in schedules:
                job_id = schedule.get('id')
                job_type = schedule.get('type')
                enabled = schedule.get('enabled', True)

                if not enabled:
                    logger.info(f"Skipping disabled job: {job_id}")
                    continue

                if job_id not in self.job_registry:
                    logger.warning(f"Job function not registered for: {job_id}")
                    continue

                job_func = self.job_registry[job_id]

                # Add job based on trigger type
                if job_type == 'cron':
                    self._add_cron_job(job_id, job_func, schedule)
                elif job_type == 'interval':
                    self._add_interval_job(job_id, job_func, schedule)
                else:
                    logger.warning(f"Unknown job type: {job_type} for job {job_id}")

            logger.info(f"Loaded {len(schedules)} schedules from configuration")
            return True

        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")
            return False

    def _add_cron_job(self, job_id: str, job_func: Callable, schedule: Dict[str, Any]) -> None:
        """Add a cron-based job.

        Args:
            job_id: Job identifier
            job_func: Job function
            schedule: Schedule configuration
        """
        try:
            cron_expr = schedule.get('cron')

            if not cron_expr:
                logger.error(f"No cron expression for job: {job_id}")
                return

            # Parse cron expression (minute hour day month day_of_week)
            parts = cron_expr.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression for job {job_id}: {cron_expr}")
                return

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=self.timezone
            )

            self.scheduler.add_job(
                job_func,
                trigger=trigger,
                id=job_id,
                name=schedule.get('name', job_id),
                replace_existing=True
            )

            logger.info(f"Added cron job: {job_id} with schedule {cron_expr}")

        except Exception as e:
            logger.error(f"Failed to add cron job {job_id}: {e}")

    def _add_interval_job(self, job_id: str, job_func: Callable, schedule: Dict[str, Any]) -> None:
        """Add an interval-based job.

        Args:
            job_id: Job identifier
            job_func: Job function
            schedule: Schedule configuration
        """
        try:
            interval_config = schedule.get('interval', {})

            if not interval_config:
                logger.error(f"No interval configuration for job: {job_id}")
                return

            # Build interval trigger
            trigger_kwargs = {}

            if 'seconds' in interval_config:
                trigger_kwargs['seconds'] = interval_config['seconds']
            if 'minutes' in interval_config:
                trigger_kwargs['minutes'] = interval_config['minutes']
            if 'hours' in interval_config:
                trigger_kwargs['hours'] = interval_config['hours']
            if 'days' in interval_config:
                trigger_kwargs['days'] = interval_config['days']

            if not trigger_kwargs:
                logger.error(f"No valid interval specified for job: {job_id}")
                return

            trigger = IntervalTrigger(**trigger_kwargs, timezone=self.timezone)

            self.scheduler.add_job(
                job_func,
                trigger=trigger,
                id=job_id,
                name=schedule.get('name', job_id),
                replace_existing=True
            )

            logger.info(f"Added interval job: {job_id} with interval {trigger_kwargs}")

        except Exception as e:
            logger.error(f"Failed to add interval job {job_id}: {e}")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task processor started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Task processor stopped")

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if job paused successfully
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.

        Args:
            job_id: Job identifier

        Returns:
            True if job resumed successfully
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: Job identifier

        Returns:
            True if job removed successfully
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False

    def get_jobs(self) -> list:
        """Get all scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []

        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return jobs

    def run_job_now(self, job_id: str) -> bool:
        """Run a job immediately (outside of schedule).

        Args:
            job_id: Job identifier

        Returns:
            True if job executed successfully
        """
        try:
            job = self.scheduler.get_job(job_id)

            if not job:
                logger.error(f"Job not found: {job_id}")
                return False

            job.func()
            logger.info(f"Executed job immediately: {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False


# Gold Tier Job Functions
# These will be registered with the task processor

def odoo_sync_job(vault_path: Path) -> None:
    """Sync Odoo transactions (every 5 minutes)."""
    logger.info("Running Odoo sync job")
    # TODO: Implement Odoo sync logic
    # This will be implemented in Phase 3 (User Story 1)


def social_metrics_job(vault_path: Path) -> None:
    """Collect social media metrics (every 6 hours)."""
    logger.info("Running social metrics collection job")
    # TODO: Implement social metrics collection
    # This will be implemented in Phase 4 (User Story 2)


def weekly_audit_job(vault_path: Path) -> None:
    """Generate weekly business audit (Sunday 6 PM)."""
    logger.info("Running weekly audit generation job")

    from src.services.audit_generator import AuditGeneratorService

    try:
        audit_service = AuditGeneratorService(vault_path)
        result = audit_service.generate_weekly_audit()

        if result.get("success"):
            logger.info(f"Weekly audit generated: {result.get('report_id')}")
        else:
            logger.error(f"Weekly audit generation failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Failed to run weekly audit job: {e}")


def mcp_health_check_job(vault_path: Path) -> None:
    """Check MCP server health (every 1 minute)."""
    logger.info("Running MCP health check job")
    # TODO: Implement MCP health check
    # This will use MCPServerOrchestrator.health_check_all()
