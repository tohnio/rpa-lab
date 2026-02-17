"""
Execution log model for RPA Lab.
Tracks task execution history and results.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of task execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PAUSED = "paused"


class ExecutionLog(BaseModel):
    """Log entry for a task execution."""
    
    id: Optional[int] = None
    task_id: int
    task_name: Optional[str] = None
    
    # Execution status
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    
    # Timing
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Execution details
    trigger_type: str = Field(default="manual")  # manual, scheduled, api
    schedule_id: Optional[int] = None
    
    # Variable values used
    variables_used: Dict[str, Any] = Field(default_factory=dict)
    
    # Results
    actions_total: int = Field(default=0)
    actions_completed: int = Field(default=0)
    actions_failed: int = Field(default=0)
    
    # Error information
    error_message: Optional[str] = None
    error_action_index: Optional[int] = None
    error_action_type: Optional[str] = None
    
    # Screenshots
    screenshot_before: Optional[str] = None  # Path to screenshot
    screenshot_after: Optional[str] = None
    screenshot_error: Optional[str] = None
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)."""
        return self.status in [
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT
        ]
    
    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.actions_total == 0:
            return 0.0
        return (self.actions_completed / self.actions_total) * 100
    
    def start(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.now()
    
    def finish(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark execution as finished."""
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        
        if success:
            self.status = ExecutionStatus.SUCCESS
        else:
            self.status = ExecutionStatus.FAILED
            self.error_message = error_message
    
    def cancel(self) -> None:
        """Mark execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
    
    def record_action(self, success: bool, action_index: int = None) -> None:
        """Record an action execution."""
        if success:
            self.actions_completed += 1
        else:
            self.actions_failed += 1
            if action_index is not None:
                self.error_action_index = action_index
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_seconds': self.duration_seconds,
            'trigger_type': self.trigger_type,
            'schedule_id': self.schedule_id,
            'variables_used': self.variables_used,
            'actions_total': self.actions_total,
            'actions_completed': self.actions_completed,
            'actions_failed': self.actions_failed,
            'error_message': self.error_message,
            'error_action_index': self.error_action_index,
            'error_action_type': self.error_action_type,
            'screenshot_before': self.screenshot_before,
            'screenshot_after': self.screenshot_after,
            'screenshot_error': self.screenshot_error,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionLog':
        """Create ExecutionLog from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'started_at', 'finished_at']:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Handle status enum
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ExecutionStatus(data['status'])
        
        return cls(**data)
    
    @classmethod
    def create_new(cls, task_id: int, task_name: str = None, 
                   trigger_type: str = "manual") -> 'ExecutionLog':
        """Create a new execution log entry."""
        return cls(
            task_id=task_id,
            task_name=task_name,
            status=ExecutionStatus.PENDING,
            trigger_type=trigger_type
        )


class ExecutionSummary(BaseModel):
    """Summary statistics for task executions."""
    
    task_id: int
    task_name: str
    
    # Counts
    total_runs: int = Field(default=0)
    successful_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)
    cancelled_runs: int = Field(default=0)
    
    # Timing
    total_duration_seconds: float = Field(default=0.0)
    average_duration_seconds: Optional[float] = None
    min_duration_seconds: Optional[float] = None
    max_duration_seconds: Optional[float] = None
    
    # Last execution
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[ExecutionStatus] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100
    
    @property
    def total_duration_formatted(self) -> str:
        """Format total duration for display."""
        if self.total_duration_seconds < 60:
            return f"{self.total_duration_seconds:.1f}s"
        elif self.total_duration_seconds < 3600:
            minutes = int(self.total_duration_seconds // 60)
            secs = int(self.total_duration_seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(self.total_duration_seconds // 3600)
            minutes = int((self.total_duration_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"