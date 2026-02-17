"""
Action recorder for RPA Lab.
Records mouse and keyboard actions for automation.
"""
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from pynput import mouse, keyboard
from pynput.keyboard import Key
from PIL import Image
import pyautogui
from loguru import logger

from src.models.action import Action, ActionType, MouseButton
from src.utils.config import config
from src.utils.helpers import save_screenshot


class Recorder:
    """
    Records user actions (mouse and keyboard) for automation tasks.
    """
    
    def __init__(self):
        self.is_recording = False
        self.actions: List[Action] = []
        self.action_callback: Optional[Callable[[Action], None]] = None
        self.stop_callback: Optional[Callable[[], None]] = None
        
        # Listeners
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.KeyboardListener] = None
        
        # Settings
        self.record_mouse_clicks = True
        self.record_mouse_moves = False
        self.record_keyboard = True
        self.record_scroll = True
        self.capture_screenshots = config.get('recording.capture_screenshots', True)
        self.screenshot_path = config.screenshot_path
        
        # Timing
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.default_delay = config.get('recording.default_delay', 0.5)
        
        # Hotkey to stop recording
        self.stop_hotkey = keyboard.Key.esc
        
        # Current keyboard state for hotkeys
        self.pressed_keys: set = set()
    
    def start_recording(self, action_callback: Optional[Callable[[Action], None]] = None,
                        stop_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Start recording user actions.
        
        Args:
            action_callback: Callback function called for each recorded action
            stop_callback: Callback function called when recording stops
        """
        if self.is_recording:
            logger.warning("Recording is already in progress")
            return
        
        self.is_recording = True
        self.actions = []
        self.action_callback = action_callback
        self.stop_callback = stop_callback
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.pressed_keys = set()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.mouse_listener.start()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.keyboard_listener.start()
        
        logger.info("Recording started - Press ESC to stop")
    
    def stop_recording(self) -> List[Action]:
        """Stop recording and return recorded actions."""
        if not self.is_recording:
            return []
        
        self.is_recording = False
        
        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        logger.info(f"Recording stopped - {len(self.actions)} actions recorded")
        
        if self.stop_callback:
            self.stop_callback()
        
        return self.actions.copy()
    
    def _calculate_delay(self) -> float:
        """Calculate delay since last action."""
        if self.last_action_time is None:
            return 0.0
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        return delay
    
    def _add_action(self, action: Action) -> None:
        """Add an action to the recording."""
        if not self.is_recording:
            return
        
        action.delay_before = self._calculate_delay()
        action.order_index = len(self.actions)
        self.actions.append(action)
        
        logger.debug(f"Recorded action: {action.action_type}")
        
        if self.action_callback:
            self.action_callback(action)
    
    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Handle mouse click events."""
        if not self.is_recording or not self.record_mouse_clicks:
            return
        
        # Only record press events, not release
        if not pressed:
            return
        
        # Map button
        btn_map = {
            mouse.Button.left: MouseButton.LEFT,
            mouse.Button.right: MouseButton.RIGHT,
            mouse.Button.middle: MouseButton.MIDDLE
        }
        btn = btn_map.get(button, MouseButton.LEFT)
        
        # Determine action type
        current_time = time.time()
        
        # Check for double click (within 300ms of last click at same position)
        if (self.actions and 
            self.actions[-1].action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK] and
            abs(self.actions[-1].x - x) < 5 and 
            abs(self.actions[-1].y - y) < 5 and
            current_time - self.last_action_time < 0.3):
            
            # Convert last click to double click
            self.actions[-1].action_type = ActionType.DOUBLE_CLICK
            logger.debug("Converted to double click")
            return
        
        # Create click action
        action = Action.create_click(x, y, btn)
        
        # Capture screenshot if enabled
        if self.capture_screenshots:
            try:
                screenshot = pyautogui.screenshot(region=(x - 25, y - 25, 50, 50))
                screenshot_path = save_screenshot(
                    screenshot, 
                    f"click_{len(self.actions)}", 
                    self.screenshot_path
                )
                action.config['screenshot'] = str(screenshot_path)
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")
        
        self._add_action(action)
    
    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll events."""
        if not self.is_recording or not self.record_scroll:
            return
        
        # dy > 0 = scroll up, dy < 0 = scroll down
        scroll_amount = dy
        action = Action.create_scroll(x, y, scroll_amount)
        self._add_action(action)
    
    def _on_press(self, key) -> None:
        """Handle key press events."""
        if not self.is_recording:
            return
        
        # Check for stop hotkey
        if key == self.stop_hotkey:
            self.stop_recording()
            return False  # Stop propagation
        
        if not self.record_keyboard:
            return
        
        # Track pressed keys for hotkey detection
        self.pressed_keys.add(key)
    
    def _on_release(self, key) -> None:
        """Handle key release events."""
        if not self.is_recording or not self.record_keyboard:
            return
        
        # Remove from pressed keys
        self.pressed_keys.discard(key)
        
        # Check if this was part of a hotkey combination
        if len(self.pressed_keys) > 0:
            return  # Wait for all keys to be released
        
        try:
            # Get the character if it's a regular key
            if hasattr(key, 'char') and key.char:
                action = Action.create_type_text(key.char)
            elif hasattr(key, 'name'):
                # Special key pressed alone
                action = Action.create_hotkey([key.name])
            else:
                return
            
            self._add_action(action)
        except Exception as e:
            logger.error(f"Error processing key release: {e}")
    
    def record_hotkey(self, keys: List[str]) -> None:
        """Record a hotkey combination (called externally)."""
        if not self.is_recording or not self.record_keyboard:
            return
        
        action = Action.create_hotkey(keys)
        self._add_action(action)
    
    def record_text(self, text: str) -> None:
        """Record typed text (called externally for bulk text)."""
        if not self.is_recording or not self.record_keyboard:
            return
        
        action = Action.create_type_text(text)
        self._add_action(action)
    
    def record_wait(self, duration: float) -> None:
        """Record a wait action."""
        if not self.is_recording:
            return
        
        action = Action.create_wait(duration)
        self._add_action(action)
    
    def record_image_click(self, image_path: str, confidence: float = 0.9) -> None:
        """Record an image-based click action."""
        if not self.is_recording:
            return
        
        action = Action.create_image_click(image_path, confidence)
        self._add_action(action)
    
    def get_action_count(self) -> int:
        """Get the number of recorded actions."""
        return len(self.actions)
    
    def clear_actions(self) -> None:
        """Clear all recorded actions."""
        self.actions = []
        logger.info("Cleared recorded actions")


class ScreenCapture:
    """
    Utility class for capturing screen regions for image recognition.
    """
    
    def __init__(self):
        self.screenshot_path = config.screenshot_path
        self.screenshot_path.mkdir(parents=True, exist_ok=True)
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Capture a specific screen region."""
        return pyautogui.screenshot(region=(x, y, width, height))
    
    def capture_full_screen(self) -> Image.Image:
        """Capture the full screen."""
        return pyautogui.screenshot()
    
    def save_image(self, image: Image.Image, name: str) -> Path:
        """Save an image to the screenshot directory."""
        return save_screenshot(image, name, self.screenshot_path)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return pyautogui.size()