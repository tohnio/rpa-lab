"""
Database manager for RPA Lab.
Provides high-level database operations using SQLAlchemy.
"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import json

from sqlalchemy import create_engine, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.database.models import (
    Base, TaskModel, ActionModel, VariableModel, 
    ScheduleModel, ExecutionLogModel, create_tables
)
from src.models.task import Task, TaskStatus
from src.models.action import Action, ActionType
from src.models.variable import Variable, VariableType
from src.models.schedule import Schedule, ScheduleType
from src.models.execution_log import ExecutionLog, ExecutionStatus
from src.utils.config import config


class DatabaseManager:
    """Database manager for RPA Lab."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = str(config.database_path)
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine and session factory
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        create_tables(self.engine)
        logger.info(f"Database initialized at {db_path}")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session as context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== TASK OPERATIONS ====================
    
    def create_task(self, task: Task) -> Task:
        """Create a new task in the database."""
        with self.get_session() as session:
            db_task = TaskModel(
                name=task.name,
                description=task.description or "",
                status=task.status.value if isinstance(task.status, TaskStatus) else task.status,
                is_active=task.is_active,
                speed_mode=task.speed_mode,
                retry_count=task.retry_count,
                retry_delay=task.retry_delay,
                tags=task.tags,
                extra_data=task.metadata
            )
            session.add(db_task)
            session.flush()
            task.id = db_task.id
            task.created_at = db_task.created_at
            task.updated_at = db_task.updated_at
            logger.info(f"Created task: {task.name} (ID: {task.id})")
            return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                return self._task_model_to_pydantic(db_task)
            return None
    
    def get_all_tasks(self, include_inactive: bool = False) -> List[Task]:
        """Get all tasks."""
        with self.get_session() as session:
            query = session.query(TaskModel)
            if not include_inactive:
                query = query.filter(TaskModel.is_active == True)
            query = query.order_by(desc(TaskModel.updated_at))
            return [self._task_model_to_pydantic(t) for t in query.all()]
    
    def update_task(self, task: Task) -> Task:
        """Update an existing task."""
        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task.id).first()
            if db_task:
                db_task.name = task.name
                db_task.description = task.description or ""
                db_task.status = task.status.value if isinstance(task.status, TaskStatus) else task.status
                db_task.is_active = task.is_active
                db_task.speed_mode = task.speed_mode
                db_task.retry_count = task.retry_count
                db_task.retry_delay = task.retry_delay
                db_task.total_runs = task.total_runs
                db_task.successful_runs = task.successful_runs
                db_task.failed_runs = task.failed_runs
                db_task.last_run_at = task.last_run_at
                db_task.tags = task.tags
                db_task.extra_data = task.metadata
                task.updated_at = datetime.now()
                db_task.updated_at = task.updated_at
                logger.info(f"Updated task: {task.name} (ID: {task.id})")
            return task
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task and all its related data."""
        with self.get_session() as session:
            db_task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                session.delete(db_task)
                logger.info(f"Deleted task ID: {task_id}")
                return True
            return False
    
    def _task_model_to_pydantic(self, db_task: TaskModel) -> Task:
        """Convert SQLAlchemy model to Pydantic model."""
        return Task(
            id=db_task.id,
            name=db_task.name,
            description=db_task.description,
            status=TaskStatus(db_task.status),
            is_active=db_task.is_active,
            speed_mode=db_task.speed_mode,
            retry_count=db_task.retry_count,
            retry_delay=db_task.retry_delay,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            last_run_at=db_task.last_run_at,
            total_runs=db_task.total_runs,
            successful_runs=db_task.successful_runs,
            failed_runs=db_task.failed_runs,
            tags=db_task.tags or [],
            metadata=db_task.extra_data or {}
        )
    
    # ==================== ACTION OPERATIONS ====================
    
    def create_action(self, action: Action) -> Action:
        """Create a new action."""
        with self.get_session() as session:
            db_action = ActionModel(
                task_id=action.task_id,
                order_index=action.order_index,
                action_type=action.action_type.value if isinstance(action.action_type, ActionType) else action.action_type,
                config=action.config,
                delay_before=action.delay_before,
                delay_after=action.delay_after,
                condition=action.condition,
                on_failure=action.on_failure,
                retry_count=action.retry_count,
                description=action.description,
                is_enabled=action.is_enabled
            )
            session.add(db_action)
            session.flush()
            action.id = db_action.id
            action.created_at = db_action.created_at
            action.updated_at = db_action.updated_at
            return action
    
    def get_task_actions(self, task_id: int) -> List[Action]:
        """Get all actions for a task, ordered by index."""
        with self.get_session() as session:
            actions = session.query(ActionModel).filter(
                ActionModel.task_id == task_id
            ).order_by(ActionModel.order_index).all()
            return [self._action_model_to_pydantic(a) for a in actions]
    
    def update_action(self, action: Action) -> Action:
        """Update an action."""
        with self.get_session() as session:
            db_action = session.query(ActionModel).filter(ActionModel.id == action.id).first()
            if db_action:
                db_action.order_index = action.order_index
                db_action.action_type = action.action_type.value if isinstance(action.action_type, ActionType) else action.action_type
                db_action.config = action.config
                db_action.delay_before = action.delay_before
                db_action.delay_after = action.delay_after
                db_action.condition = action.condition
                db_action.on_failure = action.on_failure
                db_action.retry_count = action.retry_count
                db_action.description = action.description
                db_action.is_enabled = action.is_enabled
                action.updated_at = datetime.now()
                db_action.updated_at = action.updated_at
            return action
    
    def delete_action(self, action_id: int) -> bool:
        """Delete an action."""
        with self.get_session() as session:
            db_action = session.query(ActionModel).filter(ActionModel.id == action_id).first()
            if db_action:
                session.delete(db_action)
                return True
            return False
    
    def reorder_actions(self, task_id: int, action_ids: List[int]) -> bool:
        """Reorder actions for a task."""
        with self.get_session() as session:
            for index, action_id in enumerate(action_ids):
                session.query(ActionModel).filter(
                    ActionModel.id == action_id,
                    ActionModel.task_id == task_id
                ).update({'order_index': index})
            return True
    
    def _action_model_to_pydantic(self, db_action: ActionModel) -> Action:
        """Convert SQLAlchemy model to Pydantic model."""
        return Action(
            id=db_action.id,
            task_id=db_action.task_id,
            order_index=db_action.order_index,
            action_type=ActionType(db_action.action_type),
            config=db_action.config or {},
            delay_before=db_action.delay_before,
            delay_after=db_action.delay_after,
            condition=db_action.condition,
            on_failure=db_action.on_failure,
            retry_count=db_action.retry_count,
            description=db_action.description,
            is_enabled=db_action.is_enabled,
            created_at=db_action.created_at,
            updated_at=db_action.updated_at
        )
    
    # ==================== VARIABLE OPERATIONS ====================
    
    def create_variable(self, variable: Variable) -> Variable:
        """Create a new variable."""
        with self.get_session() as session:
            db_var = VariableModel(
                task_id=variable.task_id,
                name=variable.name,
                description=variable.description,
                value_type=variable.value_type.value if isinstance(variable.value_type, VariableType) else variable.value_type,
                value=variable.value,
                default_value=variable.default_value,
                csv_path=variable.csv_path,
                csv_column=variable.csv_column,
                random_min=variable.random_min,
                random_max=variable.random_max,
                random_choices=variable.random_choices,
                timestamp_format=variable.timestamp_format,
                is_required=variable.is_required,
                is_active=variable.is_active,
                show_in_ui=variable.show_in_ui
            )
            session.add(db_var)
            session.flush()
            variable.id = db_var.id
            variable.created_at = db_var.created_at
            variable.updated_at = db_var.updated_at
            return variable
    
    def get_task_variables(self, task_id: int) -> List[Variable]:
        """Get all variables for a task."""
        with self.get_session() as session:
            variables = session.query(VariableModel).filter(
                or_(VariableModel.task_id == task_id, VariableModel.task_id == None)
            ).all()
            return [self._variable_model_to_pydantic(v) for v in variables]
    
    def get_global_variables(self) -> List[Variable]:
        """Get all global variables."""
        with self.get_session() as session:
            variables = session.query(VariableModel).filter(
                VariableModel.task_id == None
            ).all()
            return [self._variable_model_to_pydantic(v) for v in variables]
    
    def update_variable(self, variable: Variable) -> Variable:
        """Update a variable."""
        with self.get_session() as session:
            db_var = session.query(VariableModel).filter(VariableModel.id == variable.id).first()
            if db_var:
                db_var.name = variable.name
                db_var.description = variable.description
                db_var.value_type = variable.value_type.value if isinstance(variable.value_type, VariableType) else variable.value_type
                db_var.value = variable.value
                db_var.default_value = variable.default_value
                db_var.csv_path = variable.csv_path
                db_var.csv_column = variable.csv_column
                db_var.random_min = variable.random_min
                db_var.random_max = variable.random_max
                db_var.random_choices = variable.random_choices
                db_var.timestamp_format = variable.timestamp_format
                db_var.is_required = variable.is_required
                db_var.is_active = variable.is_active
                db_var.show_in_ui = variable.show_in_ui
                variable.updated_at = datetime.now()
                db_var.updated_at = variable.updated_at
            return variable
    
    def delete_variable(self, variable_id: int) -> bool:
        """Delete a variable."""
        with self.get_session() as session:
            db_var = session.query(VariableModel).filter(VariableModel.id == variable_id).first()
            if db_var:
                session.delete(db_var)
                return True
            return False
    
    def _variable_model_to_pydantic(self, db_var: VariableModel) -> Variable:
        """Convert SQLAlchemy model to Pydantic model."""
        return Variable(
            id=db_var.id,
            task_id=db_var.task_id,
            name=db_var.name,
            description=db_var.description,
            value_type=VariableType(db_var.value_type),
            value=db_var.value or "",
            default_value=db_var.default_value,
            csv_path=db_var.csv_path,
            csv_column=db_var.csv_column,
            random_min=db_var.random_min,
            random_max=db_var.random_max,
            random_choices=db_var.random_choices,
            timestamp_format=db_var.timestamp_format,
            is_required=db_var.is_required,
            is_active=db_var.is_active,
            show_in_ui=db_var.show_in_ui,
            created_at=db_var.created_at,
            updated_at=db_var.updated_at
        )
    
    # ==================== SCHEDULE OPERATIONS ====================
    
    def create_schedule(self, schedule: Schedule) -> Schedule:
        """Create a new schedule."""
        with self.get_session() as session:
            db_schedule = ScheduleModel(
                task_id=schedule.task_id,
                schedule_type=schedule.schedule_type.value if isinstance(schedule.schedule_type, ScheduleType) else schedule.schedule_type,
                schedule_config=schedule.schedule_config,
                is_active=schedule.is_active,
                last_run_at=schedule.last_run_at,
                next_run_at=schedule.next_run_at,
                max_runs=schedule.max_runs,
                run_count=schedule.run_count,
                skip_if_missed=schedule.skip_if_missed,
                max_missed_runs=schedule.max_missed_runs,
                missed_count=schedule.missed_count
            )
            session.add(db_schedule)
            session.flush()
            schedule.id = db_schedule.id
            schedule.created_at = db_schedule.created_at
            schedule.updated_at = db_schedule.updated_at
            return schedule
    
    def get_task_schedules(self, task_id: int) -> List[Schedule]:
        """Get all schedules for a task."""
        with self.get_session() as session:
            schedules = session.query(ScheduleModel).filter(
                ScheduleModel.task_id == task_id
            ).all()
            return [self._schedule_model_to_pydantic(s) for s in schedules]
    
    def get_active_schedules(self) -> List[Schedule]:
        """Get all active schedules."""
        with self.get_session() as session:
            schedules = session.query(ScheduleModel).filter(
                ScheduleModel.is_active == True
            ).all()
            return [self._schedule_model_to_pydantic(s) for s in schedules]
    
    def get_due_schedules(self) -> List[Schedule]:
        """Get schedules that are due to run."""
        now = datetime.now()
        with self.get_session() as session:
            schedules = session.query(ScheduleModel).filter(
                ScheduleModel.is_active == True,
                or_(
                    ScheduleModel.next_run_at <= now,
                    ScheduleModel.next_run_at == None
                )
            ).all()
            return [self._schedule_model_to_pydantic(s) for s in schedules]
    
    def update_schedule(self, schedule: Schedule) -> Schedule:
        """Update a schedule."""
        with self.get_session() as session:
            db_schedule = session.query(ScheduleModel).filter(ScheduleModel.id == schedule.id).first()
            if db_schedule:
                db_schedule.schedule_type = schedule.schedule_type.value if isinstance(schedule.schedule_type, ScheduleType) else schedule.schedule_type
                db_schedule.schedule_config = schedule.schedule_config
                db_schedule.is_active = schedule.is_active
                db_schedule.last_run_at = schedule.last_run_at
                db_schedule.next_run_at = schedule.next_run_at
                db_schedule.max_runs = schedule.max_runs
                db_schedule.run_count = schedule.run_count
                db_schedule.skip_if_missed = schedule.skip_if_missed
                db_schedule.max_missed_runs = schedule.max_missed_runs
                db_schedule.missed_count = schedule.missed_count
                schedule.updated_at = datetime.now()
                db_schedule.updated_at = schedule.updated_at
            return schedule
    
    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule."""
        with self.get_session() as session:
            db_schedule = session.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
            if db_schedule:
                session.delete(db_schedule)
                return True
            return False
    
    def _schedule_model_to_pydantic(self, db_schedule: ScheduleModel) -> Schedule:
        """Convert SQLAlchemy model to Pydantic model."""
        return Schedule(
            id=db_schedule.id,
            task_id=db_schedule.task_id,
            schedule_type=ScheduleType(db_schedule.schedule_type),
            schedule_config=db_schedule.schedule_config or {},
            is_active=db_schedule.is_active,
            last_run_at=db_schedule.last_run_at,
            next_run_at=db_schedule.next_run_at,
            max_runs=db_schedule.max_runs,
            run_count=db_schedule.run_count,
            skip_if_missed=db_schedule.skip_if_missed,
            max_missed_runs=db_schedule.max_missed_runs,
            missed_count=db_schedule.missed_count,
            created_at=db_schedule.created_at,
            updated_at=db_schedule.updated_at
        )
    
    # ==================== EXECUTION LOG OPERATIONS ====================
    
    def create_execution_log(self, log: ExecutionLog) -> ExecutionLog:
        """Create a new execution log."""
        with self.get_session() as session:
            db_log = ExecutionLogModel(
                task_id=log.task_id,
                task_name=log.task_name,
                status=log.status.value if isinstance(log.status, ExecutionStatus) else log.status,
                started_at=log.started_at,
                finished_at=log.finished_at,
                duration_seconds=log.duration_seconds,
                trigger_type=log.trigger_type,
                schedule_id=log.schedule_id,
                variables_used=log.variables_used,
                actions_total=log.actions_total,
                actions_completed=log.actions_completed,
                actions_failed=log.actions_failed,
                error_message=log.error_message,
                error_action_index=log.error_action_index,
                error_action_type=log.error_action_type,
                screenshot_before=log.screenshot_before,
                screenshot_after=log.screenshot_after,
                screenshot_error=log.screenshot_error,
                extra_data=log.metadata
            )
            session.add(db_log)
            session.flush()
            log.id = db_log.id
            log.created_at = db_log.created_at
            return log
    
    def get_task_execution_logs(self, task_id: int, limit: int = 100) -> List[ExecutionLog]:
        """Get execution logs for a task."""
        with self.get_session() as session:
            logs = session.query(ExecutionLogModel).filter(
                ExecutionLogModel.task_id == task_id
            ).order_by(desc(ExecutionLogModel.created_at)).limit(limit).all()
            return [self._execution_log_model_to_pydantic(l) for l in logs]
    
    def get_recent_execution_logs(self, limit: int = 50) -> List[ExecutionLog]:
        """Get recent execution logs."""
        with self.get_session() as session:
            logs = session.query(ExecutionLogModel).order_by(
                desc(ExecutionLogModel.created_at)
            ).limit(limit).all()
            return [self._execution_log_model_to_pydantic(l) for l in logs]
    
    def update_execution_log(self, log: ExecutionLog) -> ExecutionLog:
        """Update an execution log."""
        with self.get_session() as session:
            db_log = session.query(ExecutionLogModel).filter(ExecutionLogModel.id == log.id).first()
            if db_log:
                db_log.status = log.status.value if isinstance(log.status, ExecutionStatus) else log.status
                db_log.started_at = log.started_at
                db_log.finished_at = log.finished_at
                db_log.duration_seconds = log.duration_seconds
                db_log.variables_used = log.variables_used
                db_log.actions_total = log.actions_total
                db_log.actions_completed = log.actions_completed
                db_log.actions_failed = log.actions_failed
                db_log.error_message = log.error_message
                db_log.error_action_index = log.error_action_index
                db_log.error_action_type = log.error_action_type
                db_log.screenshot_before = log.screenshot_before
                db_log.screenshot_after = log.screenshot_after
                db_log.screenshot_error = log.screenshot_error
                db_log.extra_data = log.metadata
            return log
    
    def delete_old_execution_logs(self, days: int = 30) -> int:
        """Delete execution logs older than specified days."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        with self.get_session() as session:
            result = session.query(ExecutionLogModel).filter(
                ExecutionLogModel.created_at < cutoff
            ).delete()
            logger.info(f"Deleted {result} old execution logs")
            return result
    
    def _execution_log_model_to_pydantic(self, db_log: ExecutionLogModel) -> ExecutionLog:
        """Convert SQLAlchemy model to Pydantic model."""
        return ExecutionLog(
            id=db_log.id,
            task_id=db_log.task_id,
            task_name=db_log.task_name,
            status=ExecutionStatus(db_log.status),
            started_at=db_log.started_at,
            finished_at=db_log.finished_at,
            duration_seconds=db_log.duration_seconds,
            trigger_type=db_log.trigger_type,
            schedule_id=db_log.schedule_id,
            variables_used=db_log.variables_used or {},
            actions_total=db_log.actions_total,
            actions_completed=db_log.actions_completed,
            actions_failed=db_log.actions_failed,
            error_message=db_log.error_message,
            error_action_index=db_log.error_action_index,
            error_action_type=db_log.error_action_type,
            screenshot_before=db_log.screenshot_before,
            screenshot_after=db_log.screenshot_after,
            screenshot_error=db_log.screenshot_error,
            metadata=db_log.extra_data or {},
            created_at=db_log.created_at
        )


# Global database instance
db = DatabaseManager()