"""
Task model for RPA Lab.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    ARCHIVED = "archived"


class Task(BaseModel):
    """Task model representing an RPA automation task."""
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.DRAFT)
    is_active: bool = Field(default=True)
    
    # Execution settings
    speed_mode: str = Field(default="normal")  # normal, fast, turbo, instant
    retry_count: int = Field(default=0, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
    
    # Statistics
    total_runs: int = Field(default=0)
    successful_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def mark_run(self, success: bool) -> None:
        """Record a run execution."""
        self.total_runs += 1
        self.last_run_at = datetime.now()
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'is_active': self.is_active,
            'speed_mode': self.speed_mode,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'total_runs': self.total_runs,
            'successful_runs': self.successful_runs,
            'failed_runs': self.failed_runs,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create Task from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'last_run_at']:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Handle status enum
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        
        return cls(**data)