"""
Task scheduler for RPA Lab.
Handles scheduled task execution with APScheduler.
"""
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from src.models.task import Task
from src.models.schedule import Schedule, ScheduleType
from src.models.action import Action
from src.database.db_manager import db
from src.core.player import Player
from src.utils.config import config


class TaskScheduler:
    """
    Scheduler for automated task execution.
    """
    
    def __init__(self, player: Optional[Player] = None):
        self.scheduler = BackgroundScheduler()
        self.player = player or Player()
        self.is_running = False
        self._job_map: Dict[int, str] = {}  # schedule_id -> job_id
        
        # Callbacks
        self.on_task_start: Optional[Callable[[Task], None]] = None
        self.on_task_complete: Optional[Callable[[Task, bool], None]] = None
        
        # Settings
        self.check_interval = config.get('scheduler.check_interval', 60)
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler.start()
        self.is_running = True
        
        # Load all active schedules
        self._load_schedules()
        
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def _load_schedules(self) -> None:
        """Load all active schedules from database."""
        schedules = db.get_active_schedules()
        
        for schedule in schedules:
            self._add_job(schedule)
        
        logger.info(f"Loaded {len(schedules)} scheduled tasks")
    
    def _add_job(self, schedule: Schedule) -> bool:
        """Add a scheduled job."""
        try:
            # Get task and actions
            task = db.get_task(schedule.task_id)
            if not task:
                logger.error(f"Task not found for schedule {schedule.id}")
                return False
            
            actions = db.get_task_actions(schedule.task_id)
            variables = db.get_task_variables(schedule.task_id)
            
            # Create trigger based on schedule type
            trigger = self._create_trigger(schedule)
            if not trigger:
                logger.error(f"Invalid schedule configuration for {schedule.id}")
                return False
            
            # Add job
            job = self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                id=f"schedule_{schedule.id}",
                args=[schedule.id, task, actions, variables],
                name=f"Task: {task.name}",
                misfire_grace_time=300,  # 5 minutes grace period
                coalesce=True,
                max_instances=1
            )
            
            self._job_map[schedule.id] = job.id
            
            # Update next run time
            schedule.next_run_at = job.next_run_time
            db.update_schedule(schedule)
            
            logger.info(f"Added scheduled job: {task.name} (next run: {job.next_run_time})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding scheduled job: {e}")
            return False
    
    def _create_trigger(self, schedule: Schedule):
        """Create APScheduler trigger from schedule configuration."""
        try:
            time_str = schedule.time
            hour, minute = map(int, time_str.split(':'))
            
            if schedule.schedule_type == ScheduleType.DAILY:
                # Daily at specific time
                return CronTrigger(hour=hour, minute=minute)
            
            elif schedule.schedule_type == ScheduleType.WEEKLY:
                # Weekly on specific days
                days = schedule.days_of_week
                # Convert to cron day format (0=Monday in cron)
                day_of_week = ','.join([str(d) for d in days])
                return CronTrigger(
                    day_of_week=day_of_week,
                    hour=hour,
                    minute=minute
                )
            
            elif schedule.schedule_type == ScheduleType.MONTHLY:
                # Monthly on specific day
                day = schedule.day_of_month
                return CronTrigger(day=day, hour=hour, minute=minute)
            
            elif schedule.schedule_type == ScheduleType.INTERVAL:
                # Run at intervals
                minutes = schedule.interval_minutes
                return IntervalTrigger(minutes=minutes)
            
            elif schedule.schedule_type == ScheduleType.ONCE:
                # Run once at specific datetime
                run_dt = schedule.run_datetime
                if run_dt:
                    return DateTrigger(run_date=run_dt)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return None
    
    def _execute_scheduled_task(
        self,
        schedule_id: int,
        task: Task,
        actions: List[Action],
        variables: List
    ) -> None:
        """Execute a scheduled task."""
        logger.info(f"Executing scheduled task: {task.name}")
        
        # Get schedule for updating
        schedules = db.get_task_schedules(task.id)
        schedule = next((s for s in schedules if s.id == schedule_id), None)
        
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        # Notify callback
        if self.on_task_start:
            self.on_task_start(task)
        
        # Prepare variables
        var_dict = {v.name: v.get_single_value() for v in variables}
        
        # Execute task
        success = self.player.play_task(
            task=task,
            actions=actions,
            variables=var_dict,
            speed_mode=task.speed_mode,
            trigger_type="scheduled"
        )
        
        # Update schedule
        schedule.mark_run(success)
        db.update_schedule(schedule)
        
        # Update next run time from job
        job_id = self._job_map.get(schedule_id)
        if job_id:
            job = self.scheduler.get_job(job_id)
            if job:
                schedule.next_run_at = job.next_run_time
                db.update_schedule(schedule)
        
        # Notify callback
        if self.on_task_complete:
            self.on_task_complete(task, success)
    
    def add_schedule(self, schedule: Schedule) -> bool:
        """Add a new schedule."""
        return self._add_job(schedule)
    
    def remove_schedule(self, schedule_id: int) -> bool:
        """Remove a schedule."""
        job_id = self._job_map.get(schedule_id)
        
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                del self._job_map[schedule_id]
                logger.info(f"Removed schedule {schedule_id}")
                return True
            except Exception as e:
                logger.error(f"Error removing schedule: {e}")
                return False
        
        return False
    
    def update_schedule(self, schedule: Schedule) -> bool:
        """Update an existing schedule."""
        # Remove old job
        self.remove_schedule(schedule.id)
        
        # Add new job if active
        if schedule.is_active:
            return self._add_job(schedule)
        
        return True
    
    def pause_schedule(self, schedule_id: int) -> bool:
        """Pause a schedule."""
        job_id = self._job_map.get(schedule_id)
        
        if job_id:
            try:
                self.scheduler.pause_job(job_id)
                logger.info(f"Paused schedule {schedule_id}")
                return True
            except Exception as e:
                logger.error(f"Error pausing schedule: {e}")
        
        return False
    
    def resume_schedule(self, schedule_id: int) -> bool:
        """Resume a paused schedule."""
        job_id = self._job_map.get(schedule_id)
        
        if job_id:
            try:
                self.scheduler.resume_job(job_id)
                logger.info(f"Resumed schedule {schedule_id}")
                return True
            except Exception as e:
                logger.error(f"Error resuming schedule: {e}")
        
        return False
    
    def get_next_run_time(self, schedule_id: int) -> Optional[datetime]:
        """Get next run time for a schedule."""
        job_id = self._job_map.get(schedule_id)
        
        if job_id:
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time
        
        return None
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all scheduled jobs information."""
        jobs = []
        
        for schedule_id, job_id in self._job_map.items():
            job = self.scheduler.get_job(job_id)
            if job:
                jobs.append({
                    'schedule_id': schedule_id,
                    'job_id': job_id,
                    'name': job.name,
                    'next_run': job.next_run_time,
                    'trigger': str(job.trigger)
                })
        
        return jobs
    
    def reload_schedules(self) -> None:
        """Reload all schedules from database."""
        # Remove all existing jobs
        for job_id in self._job_map.values():
            try:
                self.scheduler.remove_job(job_id)
            except:
                pass
        
        self._job_map.clear()
        
        # Reload from database
        self._load_schedules()


# Global scheduler instance
task_scheduler = TaskScheduler()