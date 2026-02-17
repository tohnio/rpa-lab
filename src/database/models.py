"""
SQLAlchemy models for RPA Lab database.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, 
    ForeignKey, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for tasks table."""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="draft")
    is_active = Column(Boolean, default=True)
    
    # Execution settings
    speed_mode = Column(String(20), default="normal")
    retry_count = Column(Integer, default=0)
    retry_delay = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_run_at = Column(DateTime, nullable=True)
    
    # Statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Metadata
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)
    
    # Relationships
    actions = relationship("ActionModel", back_populates="task", cascade="all, delete-orphan")
    variables = relationship("VariableModel", back_populates="task", cascade="all, delete-orphan")
    schedules = relationship("ScheduleModel", back_populates="task", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLogModel", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', status='{self.status}')>"


class ActionModel(Base):
    """SQLAlchemy model for actions table."""
    __tablename__ = 'actions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    order_index = Column(Integer, default=0)
    
    # Action configuration
    action_type = Column(String(50), nullable=False)
    config = Column(JSON, default=dict)
    
    # Timing
    delay_before = Column(Float, default=0.0)
    delay_after = Column(Float, default=0.5)
    
    # Conditional execution
    condition = Column(Text, nullable=True)
    on_failure = Column(String(20), default="stop")
    retry_count = Column(Integer, default=0)
    
    # Description
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    task = relationship("TaskModel", back_populates="actions")
    
    def __repr__(self):
        return f"<Action(id={self.id}, type='{self.action_type}', order={self.order_index})>"


class VariableModel(Base):
    """SQLAlchemy model for variables table."""
    __tablename__ = 'variables'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)  # NULL = global
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Variable type and value
    value_type = Column(String(20), default="single")
    value = Column(Text, default="")
    default_value = Column(Text, nullable=True)
    
    # For CSV type
    csv_path = Column(Text, nullable=True)
    csv_column = Column(String(100), nullable=True)
    
    # For RANDOM type
    random_min = Column(Integer, nullable=True)
    random_max = Column(Integer, nullable=True)
    random_choices = Column(JSON, nullable=True)
    
    # For TIMESTAMP type
    timestamp_format = Column(String(100), default="%Y-%m-%d %H:%M:%S")
    
    # Options
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    show_in_ui = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    task = relationship("TaskModel", back_populates="variables")
    
    def __repr__(self):
        return f"<Variable(id={self.id}, name='{self.name}', type='{self.value_type}')>"


class ScheduleModel(Base):
    """SQLAlchemy model for schedules table."""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    
    # Schedule configuration
    schedule_type = Column(String(20), default="daily")
    schedule_config = Column(JSON, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Execution tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # Limits
    max_runs = Column(Integer, nullable=True)
    run_count = Column(Integer, default=0)
    
    # Error handling
    skip_if_missed = Column(Boolean, default=True)
    max_missed_runs = Column(Integer, default=3)
    missed_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    task = relationship("TaskModel", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, type='{self.schedule_type}', active={self.is_active})>"


class ExecutionLogModel(Base):
    """SQLAlchemy model for execution_logs table."""
    __tablename__ = 'execution_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    task_name = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Execution details
    trigger_type = Column(String(20), default="manual")
    schedule_id = Column(Integer, nullable=True)
    
    # Variables used
    variables_used = Column(JSON, default=dict)
    
    # Results
    actions_total = Column(Integer, default=0)
    actions_completed = Column(Integer, default=0)
    actions_failed = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_action_index = Column(Integer, nullable=True)
    error_action_type = Column(String(50), nullable=True)
    
    # Screenshots
    screenshot_before = Column(Text, nullable=True)
    screenshot_after = Column(Text, nullable=True)
    screenshot_error = Column(Text, nullable=True)
    
    # Additional data
    extra_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    task = relationship("TaskModel", back_populates="execution_logs")
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, task_id={self.task_id}, status='{self.status}')>"


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)