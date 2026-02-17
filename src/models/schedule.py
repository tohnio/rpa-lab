"""
Schedule model for RPA Lab.
Supports daily, weekly, and monthly scheduling.
"""
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ScheduleType(str, Enum):
    """Types of scheduling."""
    ONCE = "once"        # Run once at specific time
    DAILY = "daily"      # Run daily at specific time
    WEEKLY = "weekly"    # Run on specific days of week
    MONTHLY = "monthly"  # Run on specific day of month
    INTERVAL = "interval"  # Run at regular intervals
    CRON = "cron"        # Custom cron expression


class Schedule(BaseModel):
    """Schedule model for task automation."""
    
    id: Optional[int] = None
    task_id: int
    
    # Schedule type and configuration
    schedule_type: ScheduleType = Field(default=ScheduleType.DAILY)
    schedule_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    is_active: bool = Field(default=True)
    
    # Execution tracking
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    # Limits
    max_runs: Optional[int] = None  # Maximum number of runs (None = unlimited)
    run_count: int = Field(default=0)
    
    # Error handling
    skip_if_missed: bool = Field(default=True)  # Skip if scheduled time was missed
    max_missed_runs: int = Field(default=3)
    missed_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    @field_validator('schedule_config', mode='before')
    @classmethod
    def validate_config(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """Ensure schedule_config has required fields based on type."""
        return v or {}
    
    @property
    def time(self) -> str:
        """Get the scheduled time (HH:MM format)."""
        return self.schedule_config.get('time', '00:00')
    
    @time.setter
    def time(self, value: str) -> None:
        """Set the scheduled time."""
        self.schedule_config['time'] = value
    
    @property
    def days_of_week(self) -> List[int]:
        """Get days of week for weekly schedule (0=Monday, 6=Sunday)."""
        return self.schedule_config.get('days_of_week', [0])
    
    @days_of_week.setter
    def days_of_week(self, value: List[int]) -> None:
        """Set days of week for weekly schedule."""
        self.schedule_config['days_of_week'] = value
    
    @property
    def day_of_month(self) -> int:
        """Get day of month for monthly schedule (1-31)."""
        return self.schedule_config.get('day_of_month', 1)
    
    @day_of_month.setter
    def day_of_month(self, value: int) -> None:
        """Set day of month for monthly schedule."""
        self.schedule_config['day_of_month'] = value
    
    @property
    def interval_minutes(self) -> int:
        """Get interval in minutes for interval schedule."""
        return self.schedule_config.get('interval_minutes', 60)
    
    @interval_minutes.setter
    def interval_minutes(self, value: int) -> None:
        """Set interval in minutes."""
        self.schedule_config['interval_minutes'] = value
    
    @property
    def run_datetime(self) -> Optional[datetime]:
        """Get the specific datetime for 'once' schedule."""
        dt_str = self.schedule_config.get('run_datetime')
        if dt_str:
            return datetime.fromisoformat(dt_str)
        return None
    
    @run_datetime.setter
    def run_datetime(self, value: datetime) -> None:
        """Set the specific datetime for 'once' schedule."""
        self.schedule_config['run_datetime'] = value.isoformat()
    
    def calculate_next_run(self, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next run time based on schedule configuration.
        
        Args:
            from_time: Base time to calculate from (defaults to now)
        
        Returns:
            Next scheduled datetime or None if no more runs
        """
        if not self.is_active:
            return None
        
        if self.max_runs and self.run_count >= self.max_runs:
            return None
        
        if from_time is None:
            from_time = datetime.now()
        
        try:
            hour, minute = map(int, self.time.split(':'))
        except (ValueError, AttributeError):
            hour, minute = 0, 0
        
        if self.schedule_type == ScheduleType.ONCE:
            run_dt = self.run_datetime
            if run_dt and run_dt > from_time:
                return run_dt
            return None
        
        elif self.schedule_type == ScheduleType.DAILY:
            # Next occurrence of the scheduled time
            next_run = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= from_time:
                next_run += timedelta(days=1)
            return next_run
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            # Find next matching day of week
            next_run = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days = sorted(self.days_of_week) if self.days_of_week else [0]
            
            for _ in range(8):  # Check up to 7 days ahead
                if next_run.weekday() in days and next_run > from_time:
                    return next_run
                next_run += timedelta(days=1)
            
            return next_run
        
        elif self.schedule_type == ScheduleType.MONTHLY:
            # Find next occurrence of the day of month
            target_day = min(self.day_of_month, 28)  # Safe day for all months
            
            next_run = from_time.replace(day=target_day, hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_run <= from_time:
                # Move to next month
                if from_time.month == 12:
                    next_run = next_run.replace(year=from_time.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=from_time.month + 1)
            
            return next_run
        
        elif self.schedule_type == ScheduleType.INTERVAL:
            # Run at regular intervals
            if self.last_run_at:
                return self.last_run_at + timedelta(minutes=self.interval_minutes)
            else:
                return from_time
        
        elif self.schedule_type == ScheduleType.CRON:
            # Cron expression handling would require croniter library
            # For now, return None
            return None
        
        return None
    
    def mark_run(self, success: bool = True) -> None:
        """Record a run execution."""
        self.last_run_at = datetime.now()
        self.run_count += 1
        self.missed_count = 0  # Reset missed count on successful run
        self.next_run_at = self.calculate_next_run()
        self.update_timestamp()
    
    def mark_missed(self) -> None:
        """Record a missed run."""
        self.missed_count += 1
        if self.missed_count >= self.max_missed_runs:
            self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'schedule_type': self.schedule_type.value if isinstance(self.schedule_type, ScheduleType) else self.schedule_type,
            'schedule_config': self.schedule_config,
            'is_active': self.is_active,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'max_runs': self.max_runs,
            'run_count': self.run_count,
            'skip_if_missed': self.skip_if_missed,
            'max_missed_runs': self.max_missed_runs,
            'missed_count': self.missed_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Create Schedule from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'last_run_at', 'next_run_at']:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Handle schedule_type enum
        if 'schedule_type' in data and isinstance(data['schedule_type'], str):
            data['schedule_type'] = ScheduleType(data['schedule_type'])
        
        return cls(**data)
    
    @classmethod
    def create_daily(cls, task_id: int, time_str: str) -> 'Schedule':
        """Factory method to create a daily schedule."""
        schedule = cls(task_id=task_id, schedule_type=ScheduleType.DAILY)
        schedule.time = time_str
        schedule.next_run_at = schedule.calculate_next_run()
        return schedule
    
    @classmethod
    def create_weekly(cls, task_id: int, time_str: str, days: List[int]) -> 'Schedule':
        """Factory method to create a weekly schedule."""
        schedule = cls(task_id=task_id, schedule_type=ScheduleType.WEEKLY)
        schedule.time = time_str
        schedule.days_of_week = days
        schedule.next_run_at = schedule.calculate_next_run()
        return schedule
    
    @classmethod
    def create_monthly(cls, task_id: int, time_str: str, day: int) -> 'Schedule':
        """Factory method to create a monthly schedule."""
        schedule = cls(task_id=task_id, schedule_type=ScheduleType.MONTHLY)
        schedule.time = time_str
        schedule.day_of_month = day
        schedule.next_run_at = schedule.calculate_next_run()
        return schedule
    
    @classmethod
    def create_interval(cls, task_id: int, interval_minutes: int) -> 'Schedule':
        """Factory method to create an interval schedule."""
        schedule = cls(task_id=task_id, schedule_type=ScheduleType.INTERVAL)
        schedule.interval_minutes = interval_minutes
        schedule.next_run_at = schedule.calculate_next_run()
        return schedule