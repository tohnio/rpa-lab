"""
Configuration manager for RPA Lab.
Loads and manages application settings from YAML file.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager class."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from YAML file."""
        if config_path is None:
            # Default config path
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config.yaml"
        
        config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # Use default configuration
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'app': {
                'name': 'RPA Lab',
                'version': '1.0.0',
                'language': 'pt-BR',
                'theme': 'dark'
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/rpa.db'
            },
            'recording': {
                'default_delay': 0.5,
                'capture_screenshots': True,
                'screenshot_quality': 85,
                'screenshot_path': 'data/screenshots'
            },
            'execution': {
                'default_speed': 'normal',
                'speeds': {
                    'normal': 1.0,
                    'fast': 0.5,
                    'turbo': 0.1,
                    'instant': 0.0
                },
                'retry_on_failure': 3,
                'retry_delay': 1.0
            },
            'image_recognition': {
                'default_confidence': 0.9,
                'grayscale': True,
                'search_area': 'full_screen'
            },
            'scheduler': {
                'check_interval': 60,
                'max_concurrent_tasks': 1,
                'log_retention_days': 30
            },
            'ui': {
                'window_width': 1200,
                'window_height': 800,
                'sidebar_width': 250,
                'show_notifications': True
            },
            'logging': {
                'level': 'INFO',
                'path': 'logs',
                'max_file_size': '10 MB',
                'retention': '7 days'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        Example: config.get('app.name')
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        Example: config.set('app.theme', 'light')
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def app_name(self) -> str:
        return self.get('app.name', 'RPA Lab')
    
    @property
    def app_version(self) -> str:
        return self.get('app.version', '1.0.0')
    
    @property
    def theme(self) -> str:
        return self.get('app.theme', 'dark')
    
    @property
    def database_path(self) -> Path:
        base_dir = Path(__file__).parent.parent.parent
        db_path = self.get('database.path', 'data/rpa.db')
        return base_dir / db_path
    
    @property
    def screenshot_path(self) -> Path:
        base_dir = Path(__file__).parent.parent.parent
        path = self.get('recording.screenshot_path', 'data/screenshots')
        return base_dir / path
    
    @property
    def log_path(self) -> Path:
        base_dir = Path(__file__).parent.parent.parent
        path = self.get('logging.path', 'logs')
        return base_dir / path
    
    @property
    def speeds(self) -> Dict[str, float]:
        return self.get('execution.speeds', {
            'normal': 1.0,
            'fast': 0.5,
            'turbo': 0.1,
            'instant': 0.0
        })
    
    @property
    def default_speed(self) -> str:
        return self.get('execution.default_speed', 'normal')
    
    @property
    def image_confidence(self) -> float:
        return self.get('image_recognition.default_confidence', 0.9)
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        dirs = [
            self.database_path.parent,
            self.screenshot_path,
            self.log_path
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()