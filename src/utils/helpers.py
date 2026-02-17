"""
Helper functions and utilities for RPA Lab.
"""
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import io
import base64


def parse_variables(text: str) -> List[str]:
    """
    Extract variable names from text.
    Variables are in format {{variable_name}}
    
    Returns list of variable names found.
    """
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, text)
    return list(set(matches))


def replace_variables(text: str, variables: Dict[str, Any]) -> str:
    """
    Replace variables in text with their values.
    
    Args:
        text: Text containing {{variable}} placeholders
        variables: Dictionary mapping variable names to values
    
    Returns:
        Text with variables replaced
    """
    def replacer(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    pattern = r'\{\{(\w+)\}\}'
    return re.sub(pattern, replacer, text)


def screenshot_to_base64(screenshot: Image.Image, quality: int = 85) -> str:
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    screenshot.save(buffer, format='PNG', quality=quality)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def base64_to_image(base64_string: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))


def save_screenshot(screenshot: Image.Image, name: str, path: Path) -> Path:
    """
    Save screenshot to disk with timestamp.
    
    Returns the path to saved file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = path / filename
    path.mkdir(parents=True, exist_ok=True)
    screenshot.save(filepath, 'PNG')
    return filepath


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_schedule(schedule_type: str, schedule_config: Dict) -> str:
    """Format schedule for display."""
    if schedule_type == 'daily':
        return f"Diariamente às {schedule_config.get('time', '00:00')}"
    elif schedule_type == 'weekly':
        days = schedule_config.get('days_of_week', [])
        day_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        days_str = ', '.join([day_names[d] for d in days if 0 <= d < 7])
        return f"Semanal ({days_str}) às {schedule_config.get('time', '00:00')}"
    elif schedule_type == 'monthly':
        day = schedule_config.get('day_of_month', 1)
        return f"Mensal (dia {day}) às {schedule_config.get('time', '00:00')}"
    return "Sem agendamento"


def validate_json(json_str: str) -> Tuple[bool, Optional[Dict]]:
    """Validate JSON string and return parsed dict if valid."""
    try:
        data = json.loads(json_str)
        return True, data
    except json.JSONDecodeError:
        return False, None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def get_screen_size() -> Tuple[int, int]:
    """Get the screen resolution."""
    try:
        import pyautogui
        return pyautogui.size()
    except:
        return (1920, 1080)  # Default fallback


def ensure_path_exists(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)