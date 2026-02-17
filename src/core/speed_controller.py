"""
Speed controller for RPA Lab execution.
Adjusts delays between actions based on speed mode.
"""
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger

from src.utils.config import config


class SpeedMode(str, Enum):
    """Speed modes for execution."""
    NORMAL = "normal"
    FAST = "fast"
    TURBO = "turbo"
    INSTANT = "instant"


@dataclass
class SpeedSettings:
    """Settings for a speed mode."""
    name: str
    multiplier: float
    min_delay: float
    description: str


class SpeedController:
    """
    Controls execution speed by adjusting delays between actions.
    """
    
    # Default speed settings
    DEFAULT_SPEEDS = {
        SpeedMode.NORMAL: SpeedSettings(
            name="normal",
            multiplier=1.0,
            min_delay=0.1,
            description="Velocidade normal - execução em tempo real"
        ),
        SpeedMode.FAST: SpeedSettings(
            name="fast",
            multiplier=0.5,
            min_delay=0.05,
            description="Velocidade rápida - 2x mais rápido"
        ),
        SpeedMode.TURBO: SpeedSettings(
            name="turbo",
            multiplier=0.1,
            min_delay=0.01,
            description="Velocidade turbo - 10x mais rápido"
        ),
        SpeedMode.INSTANT: SpeedSettings(
            name="instant",
            multiplier=0.0,
            min_delay=0.0,
            description="Instantâneo - sem delays"
        )
    }
    
    def __init__(self):
        self.speeds = self._load_speed_settings()
        self.current_mode = SpeedMode(config.default_speed)
        self._speed_multiplier = self.speeds[self.current_mode].multiplier
        self._min_delay = self.speeds[self.current_mode].min_delay
    
    def _load_speed_settings(self) -> Dict[SpeedMode, SpeedSettings]:
        """Load speed settings from config or use defaults."""
        speeds = {}
        config_speeds = config.speeds
        
        for mode in SpeedMode:
            if mode.value in config_speeds:
                multiplier = config_speeds[mode.value]
                speeds[mode] = SpeedSettings(
                    name=mode.value,
                    multiplier=multiplier,
                    min_delay=0.01 if multiplier < 0.5 else 0.1,
                    description=self.DEFAULT_SPEEDS[mode].description
                )
            else:
                speeds[mode] = self.DEFAULT_SPEEDS[mode]
        
        return speeds
    
    def set_speed(self, mode: SpeedMode) -> None:
        """Set the current speed mode."""
        self.current_mode = mode
        settings = self.speeds[mode]
        self._speed_multiplier = settings.multiplier
        self._min_delay = settings.min_delay
        logger.info(f"Speed set to {mode.value} (multiplier: {settings.multiplier})")
    
    def get_speed(self) -> SpeedMode:
        """Get the current speed mode."""
        return self.current_mode
    
    def adjust_delay(self, delay: float) -> float:
        """
        Adjust a delay value based on current speed mode.
        
        Args:
            delay: Original delay in seconds
        
        Returns:
            Adjusted delay in seconds
        """
        if self._speed_multiplier == 0:
            # Instant mode - no delay
            return 0.0
        
        adjusted = delay * self._speed_multiplier
        
        # Apply minimum delay if not instant
        if adjusted > 0:
            adjusted = max(adjusted, self._min_delay)
        
        return adjusted
    
    def get_wait_time(self, original_wait: float) -> float:
        """
        Get adjusted wait time for explicit wait actions.
        
        For explicit wait actions, we still apply the speed multiplier,
        but with a higher minimum to prevent issues.
        """
        if self._speed_multiplier == 0:
            return 0.01  # Minimal wait for stability
        
        adjusted = original_wait * self._speed_multiplier
        return max(adjusted, 0.01)
    
    def get_typing_speed(self) -> float:
        """
        Get typing interval based on speed mode.
        
        Returns:
            Interval between keystrokes in seconds
        """
        intervals = {
            SpeedMode.NORMAL: 0.05,  # 20 chars/sec
            SpeedMode.FAST: 0.02,    # 50 chars/sec
            SpeedMode.TURBO: 0.005,  # 200 chars/sec
            SpeedMode.INSTANT: 0.0   # As fast as possible
        }
        return intervals.get(self.current_mode, 0.05)
    
    def get_mouse_duration(self) -> float:
        """
        Get mouse movement duration based on speed mode.
        
        Returns:
            Duration for mouse movements in seconds
        """
        durations = {
            SpeedMode.NORMAL: 0.3,
            SpeedMode.FAST: 0.15,
            SpeedMode.TURBO: 0.05,
            SpeedMode.INSTANT: 0.0
        }
        return durations.get(self.current_mode, 0.3)
    
    def get_scroll_duration(self) -> float:
        """Get scroll pause duration based on speed mode."""
        durations = {
            SpeedMode.NORMAL: 0.5,
            SpeedMode.FAST: 0.25,
            SpeedMode.TURBO: 0.1,
            SpeedMode.INSTANT: 0.0
        }
        return durations.get(self.current_mode, 0.5)
    
    def get_settings(self, mode: SpeedMode) -> SpeedSettings:
        """Get settings for a specific speed mode."""
        return self.speeds.get(mode, self.DEFAULT_SPEEDS[mode])
    
    def get_all_settings(self) -> Dict[SpeedMode, SpeedSettings]:
        """Get all speed settings."""
        return self.speeds.copy()
    
    @property
    def multiplier(self) -> float:
        """Get current speed multiplier."""
        return self._speed_multiplier
    
    @property
    def is_instant(self) -> bool:
        """Check if current mode is instant."""
        return self.current_mode == SpeedMode.INSTANT or self._speed_multiplier == 0
    
    def __str__(self) -> str:
        return f"SpeedController(mode={self.current_mode.value}, multiplier={self._speed_multiplier})"