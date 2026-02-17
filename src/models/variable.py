"""
Variable model for RPA Lab.
Supports variable substitution in task actions.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class VariableType(str, Enum):
    """Types of variables."""
    SINGLE = "single"       # Single value
    LIST = "list"           # List of values (iterate during execution)
    CSV = "csv"             # Import from CSV file
    RANDOM = "random"       # Random value from a range or list
    TIMESTAMP = "timestamp" # Current timestamp
    ENVIRONMENT = "env"     # Environment variable


class Variable(BaseModel):
    """Variable model for task parameterization."""
    
    id: Optional[int] = None
    task_id: Optional[int] = None  # NULL = global variable
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^\w+$')
    description: Optional[str] = Field(default=None, max_length=500)
    
    # Variable type and value
    value_type: VariableType = Field(default=VariableType.SINGLE)
    value: str = Field(default="")
    default_value: Optional[str] = Field(default=None)
    
    # For CSV type
    csv_path: Optional[str] = None
    csv_column: Optional[str] = None
    
    # For RANDOM type
    random_min: Optional[int] = None
    random_max: Optional[int] = None
    random_choices: Optional[List[str]] = None
    
    # For TIMESTAMP type
    timestamp_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    
    # Options
    is_required: bool = Field(default=False)
    is_active: bool = Field(default=True)
    show_in_ui: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure variable name is valid."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Variable name must contain only letters, numbers, and underscores')
        return v.lower()
    
    def get_values(self) -> List[str]:
        """
        Get all values for this variable.
        Returns a list of values (single item for SINGLE type).
        """
        if self.value_type == VariableType.SINGLE:
            return [self.value] if self.value else [self.default_value or ""]
        
        elif self.value_type == VariableType.LIST:
            # Parse comma or newline separated values
            if not self.value:
                return []
            values = [v.strip() for v in self.value.replace('\n', ',').split(',') if v.strip()]
            return values
        
        elif self.value_type == VariableType.CSV:
            # Will be handled by CSV loader
            return [self.value]
        
        elif self.value_type == VariableType.RANDOM:
            return [self.value]  # Placeholder
        
        elif self.value_type == VariableType.TIMESTAMP:
            from datetime import datetime as dt
            return [dt.now().strftime(self.timestamp_format)]
        
        elif self.value_type == VariableType.ENVIRONMENT:
            import os
            return [os.environ.get(self.value, self.default_value or "")]
        
        return [self.value or ""]
    
    def get_single_value(self) -> str:
        """Get a single value (first from list)."""
        values = self.get_values()
        return values[0] if values else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'value_type': self.value_type.value if isinstance(self.value_type, VariableType) else self.value_type,
            'value': self.value,
            'default_value': self.default_value,
            'csv_path': self.csv_path,
            'csv_column': self.csv_column,
            'random_min': self.random_min,
            'random_max': self.random_max,
            'random_choices': self.random_choices,
            'timestamp_format': self.timestamp_format,
            'is_required': self.is_required,
            'is_active': self.is_active,
            'show_in_ui': self.show_in_ui,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Variable':
        """Create Variable from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at']:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Handle value_type enum
        if 'value_type' in data and isinstance(data['value_type'], str):
            data['value_type'] = VariableType(data['value_type'])
        
        return cls(**data)


class VariableSet(BaseModel):
    """Collection of variables for a task execution."""
    
    variables: Dict[str, Variable] = Field(default_factory=dict)
    
    def add(self, variable: Variable) -> None:
        """Add a variable to the set."""
        self.variables[variable.name] = variable
    
    def get(self, name: str, default: str = "") -> str:
        """Get variable value by name."""
        if name in self.variables:
            return self.variables[name].get_single_value()
        return default
    
    def get_all_values(self, name: str) -> List[str]:
        """Get all values for a variable (for iteration)."""
        if name in self.variables:
            return self.variables[name].get_values()
        return []
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to simple name-value dictionary."""
        return {name: var.get_single_value() for name, var in self.variables.items()}
    
    @classmethod
    def from_list(cls, variables: List[Variable]) -> 'VariableSet':
        """Create VariableSet from list of variables."""
        var_dict = {v.name: v for v in variables}
        return cls(variables=var_dict)