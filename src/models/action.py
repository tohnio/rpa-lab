"""
Action model for RPA Lab.
Represents individual automation actions within a task.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of automation actions."""
    # Mouse actions
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    MOVE_TO = "move_to"
    SCROLL = "scroll"
    
    # Image-based actions
    IMAGE_CLICK = "image_click"
    IMAGE_WAIT = "image_wait"
    IMAGE_EXISTS = "image_exists"
    
    # Keyboard actions
    TYPE_TEXT = "type_text"
    KEY_PRESS = "key_press"
    HOTKEY = "hotkey"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    
    # Control actions
    WAIT = "wait"
    PAUSE = "pause"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    
    # Screen actions
    SCREENSHOT = "screenshot"
    COPY_TEXT = "copy_text"


class MouseButton(str, Enum):
    """Mouse button options."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class Action(BaseModel):
    """Action model representing a single automation action."""
    
    id: Optional[int] = None
    task_id: Optional[int] = None
    order_index: int = Field(default=0, ge=0)
    
    # Action type and configuration
    action_type: ActionType
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing
    delay_before: float = Field(default=0.0, ge=0, description="Seconds to wait before action")
    delay_after: float = Field(default=0.5, ge=0, description="Seconds to wait after action")
    
    # Conditional execution
    condition: Optional[str] = Field(default=None, description="Optional condition expression")
    on_failure: str = Field(default="stop", description="What to do on failure: stop, skip, retry")
    retry_count: int = Field(default=0, ge=0)
    
    # Description and metadata
    description: Optional[str] = Field(default=None)
    is_enabled: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    @property
    def x(self) -> Optional[int]:
        """Get X coordinate from config."""
        return self.config.get('x')
    
    @x.setter
    def x(self, value: int) -> None:
        """Set X coordinate in config."""
        self.config['x'] = value
    
    @property
    def y(self) -> Optional[int]:
        """Get Y coordinate from config."""
        return self.config.get('y')
    
    @y.setter
    def y(self, value: int) -> None:
        """Set Y coordinate in config."""
        self.config['y'] = value
    
    @property
    def text(self) -> Optional[str]:
        """Get text from config."""
        return self.config.get('text')
    
    @text.setter
    def text(self, value: str) -> None:
        """Set text in config."""
        self.config['text'] = value
    
    @property
    def image_path(self) -> Optional[str]:
        """Get image path from config."""
        return self.config.get('image_path')
    
    @image_path.setter
    def image_path(self, value: str) -> None:
        """Set image path in config."""
        self.config['image_path'] = value
    
    @property
    def confidence(self) -> float:
        """Get image matching confidence."""
        return self.config.get('confidence', 0.9)
    
    @confidence.setter
    def confidence(self, value: float) -> None:
        """Set image matching confidence."""
        self.config['confidence'] = value
    
    @property
    def button(self) -> MouseButton:
        """Get mouse button from config."""
        btn = self.config.get('button', 'left')
        return MouseButton(btn) if isinstance(btn, str) else btn
    
    @button.setter
    def button(self, value: MouseButton) -> None:
        """Set mouse button in config."""
        self.config['button'] = value.value if isinstance(value, MouseButton) else value
    
    @property
    def keys(self) -> List[str]:
        """Get keys for hotkey action."""
        return self.config.get('keys', [])
    
    @keys.setter
    def keys(self, value: List[str]) -> None:
        """Set keys for hotkey action."""
        self.config['keys'] = value
    
    @property
    def duration(self) -> float:
        """Get duration for wait action."""
        return self.config.get('duration', 1.0)
    
    @duration.setter
    def duration(self, value: float) -> None:
        """Set duration for wait action."""
        self.config['duration'] = value
    
    @property
    def scroll_amount(self) -> int:
        """Get scroll amount (positive for up, negative for down)."""
        return self.config.get('scroll_amount', 0)
    
    @scroll_amount.setter
    def scroll_amount(self, value: int) -> None:
        """Set scroll amount."""
        self.config['scroll_amount'] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'order_index': self.order_index,
            'action_type': self.action_type.value if isinstance(self.action_type, ActionType) else self.action_type,
            'config': self.config,
            'delay_before': self.delay_before,
            'delay_after': self.delay_after,
            'condition': self.condition,
            'on_failure': self.on_failure,
            'retry_count': self.retry_count,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create Action from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at']:
            if data.get(field) and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Handle action_type enum
        if 'action_type' in data and isinstance(data['action_type'], str):
            data['action_type'] = ActionType(data['action_type'])
        
        return cls(**data)
    
    @classmethod
    def create_click(cls, x: int, y: int, button: MouseButton = MouseButton.LEFT, 
                     delay_after: float = 0.5) -> 'Action':
        """Factory method to create a click action."""
        return cls(
            action_type=ActionType.CLICK,
            config={'x': x, 'y': y, 'button': button.value},
            delay_after=delay_after
        )
    
    @classmethod
    def create_double_click(cls, x: int, y: int, delay_after: float = 0.5) -> 'Action':
        """Factory method to create a double click action."""
        return cls(
            action_type=ActionType.DOUBLE_CLICK,
            config={'x': x, 'y': y, 'button': 'left'},
            delay_after=delay_after
        )
    
    @classmethod
    def create_right_click(cls, x: int, y: int, delay_after: float = 0.5) -> 'Action':
        """Factory method to create a right click action."""
        return cls(
            action_type=ActionType.RIGHT_CLICK,
            config={'x': x, 'y': y},
            delay_after=delay_after
        )
    
    @classmethod
    def create_type_text(cls, text: str, delay_after: float = 0.5) -> 'Action':
        """Factory method to create a type text action."""
        return cls(
            action_type=ActionType.TYPE_TEXT,
            config={'text': text},
            delay_after=delay_after
        )
    
    @classmethod
    def create_hotkey(cls, keys: List[str], delay_after: float = 0.5) -> 'Action':
        """Factory method to create a hotkey action."""
        return cls(
            action_type=ActionType.HOTKEY,
            config={'keys': keys},
            delay_after=delay_after
        )
    
    @classmethod
    def create_wait(cls, duration: float) -> 'Action':
        """Factory method to create a wait action."""
        return cls(
            action_type=ActionType.WAIT,
            config={'duration': duration},
            delay_after=0
        )
    
    @classmethod
    def create_image_click(cls, image_path: str, confidence: float = 0.9, 
                           delay_after: float = 0.5) -> 'Action':
        """Factory method to create an image click action."""
        return cls(
            action_type=ActionType.IMAGE_CLICK,
            config={'image_path': image_path, 'confidence': confidence},
            delay_after=delay_after
        )
    
    @classmethod
    def create_scroll(cls, x: int, y: int, scroll_amount: int, 
                      delay_after: float = 0.5) -> 'Action':
        """Factory method to create a scroll action."""
        return cls(
            action_type=ActionType.SCROLL,
            config={'x': x, 'y': y, 'scroll_amount': scroll_amount},
            delay_after=delay_after
        )