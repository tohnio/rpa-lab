"""
Action player/executor for RPA Lab.
Executes recorded actions with variable substitution and speed control.
"""
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pyautogui
from loguru import logger

from src.models.action import Action, ActionType, MouseButton
from src.models.task import Task
from src.models.variable import Variable
from src.models.execution_log import ExecutionLog, ExecutionStatus
from src.core.image_recognition import ImageRecognition
from src.core.speed_controller import SpeedController, SpeedMode
from src.database.db_manager import db
from src.utils.config import config
from src.utils.helpers import replace_variables, parse_variables


class Player:
    """
    Executes automation tasks by playing recorded actions.
    """
    
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.current_task: Optional[Task] = None
        self.current_action_index: int = 0
        self.variables: Dict[str, str] = {}
        
        # Components
        self.image_recognition = ImageRecognition()
        self.speed_controller = SpeedController()
        
        # Callbacks
        self.on_action_start: Optional[Callable[[Action, int], None]] = None
        self.on_action_complete: Optional[Callable[[Action, int, bool], None]] = None
        self.on_task_complete: Optional[Callable[[Task, bool], None]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None
        
        # Execution state
        self._stop_flag = False
        self._pause_flag = False
        self._execution_log: Optional[ExecutionLog] = None
        
        # Settings
        self.retry_on_failure = config.get('execution.retry_on_failure', 3)
        self.retry_delay = config.get('execution.retry_delay', 1.0)
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
    
    def play_task(
        self,
        task: Task,
        actions: List[Action],
        variables: Optional[Dict[str, str]] = None,
        speed_mode: Optional[str] = None,
        trigger_type: str = "manual"
    ) -> bool:
        """
        Execute a task with given actions.
        
        Args:
            task: Task to execute
            actions: List of actions to perform
            variables: Variable values for substitution
            speed_mode: Speed mode for execution
            trigger_type: How the task was triggered (manual, scheduled)
        
        Returns:
            True if execution completed successfully
        """
        if self.is_running:
            logger.warning("Another task is already running")
            return False
        
        self.is_running = True
        self.is_paused = False
        self._stop_flag = False
        self._pause_flag = False
        self.current_task = task
        self.current_action_index = 0
        self.variables = variables or {}
        
        # Set speed mode
        if speed_mode:
            self.speed_controller.set_speed(SpeedMode(speed_mode))
        
        # Create execution log
        self._execution_log = ExecutionLog.create_new(
            task_id=task.id,
            task_name=task.name,
            trigger_type=trigger_type
        )
        self._execution_log.actions_total = len(actions)
        self._execution_log.started_at = datetime.now()
        self._execution_log.status = ExecutionStatus.RUNNING
        self._execution_log.variables_used = self.variables
        
        # Save initial log
        self._execution_log = db.create_execution_log(self._execution_log)
        
        logger.info(f"Starting task: {task.name} ({len(actions)} actions)")
        
        success = True
        
        try:
            for i, action in enumerate(actions):
                if self._stop_flag:
                    logger.info("Execution stopped by user")
                    success = False
                    break
                
                while self._pause_flag:
                    self.is_paused = True
                    time.sleep(0.1)
                self.is_paused = False
                
                self.current_action_index = i
                
                # Check if action is enabled
                if not action.is_enabled:
                    logger.debug(f"Skipping disabled action {i}")
                    continue
                
                # Notify callback
                if self.on_action_start:
                    self.on_action_start(action, i)
                
                # Notify progress
                if self.on_progress:
                    self.on_progress(i + 1, len(actions))
                
                # Execute action
                action_success = self._execute_action(action, i)
                
                # Update log
                self._execution_log.record_action(action_success, i)
                
                # Notify callback
                if self.on_action_complete:
                    self.on_action_complete(action, i, action_success)
                
                if not action_success:
                    if action.on_failure == "stop":
                        success = False
                        break
                    elif action.on_failure == "retry":
                        # Retry logic
                        for retry in range(action.retry_count):
                            logger.info(f"Retrying action {i} (attempt {retry + 1})")
                            time.sleep(self.retry_delay)
                            action_success = self._execute_action(action, i)
                            if action_success:
                                break
                        
                        if not action_success and action.on_failure != "skip":
                            success = False
                            break
                
                # Update log after each action
                db.update_execution_log(self._execution_log)
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            success = False
            self._execution_log.error_message = str(e)
            self._execution_log.error_action_index = self.current_action_index
        
        finally:
            # Finalize execution log
            self._execution_log.finish(success)
            db.update_execution_log(self._execution_log)
            
            # Update task statistics
            task.mark_run(success)
            db.update_task(task)
            
            self.is_running = False
            self.current_task = None
            
            logger.info(f"Task completed: {task.name} (success={success})")
            
            if self.on_task_complete:
                self.on_task_complete(task, success)
        
        return success
    
    def play_task_async(
        self,
        task: Task,
        actions: List[Action],
        variables: Optional[Dict[str, str]] = None,
        speed_mode: Optional[str] = None,
        trigger_type: str = "manual"
    ) -> threading.Thread:
        """Execute a task in a background thread."""
        thread = threading.Thread(
            target=self.play_task,
            args=(task, actions, variables, speed_mode, trigger_type),
            daemon=True
        )
        thread.start()
        return thread
    
    def stop(self) -> None:
        """Stop the current execution."""
        if self.is_running:
            logger.info("Stopping execution...")
            self._stop_flag = True
    
    def pause(self) -> None:
        """Pause the current execution."""
        if self.is_running and not self.is_paused:
            logger.info("Pausing execution...")
            self._pause_flag = True
    
    def resume(self) -> None:
        """Resume paused execution."""
        if self.is_paused:
            logger.info("Resuming execution...")
            self._pause_flag = False
    
    def _execute_action(self, action: Action, index: int) -> bool:
        """
        Execute a single action.
        
        Returns:
            True if action executed successfully
        """
        try:
            # Delay before action
            delay_before = self.speed_controller.adjust_delay(action.delay_before)
            if delay_before > 0:
                time.sleep(delay_before)
            
            action_type = action.action_type
            
            # Process variable substitution in config
            processed_config = self._process_config(action.config)
            
            # Execute based on action type
            if action_type == ActionType.CLICK:
                self._do_click(processed_config)
            elif action_type == ActionType.DOUBLE_CLICK:
                self._do_double_click(processed_config)
            elif action_type == ActionType.RIGHT_CLICK:
                self._do_right_click(processed_config)
            elif action_type == ActionType.MOVE_TO:
                self._do_move_to(processed_config)
            elif action_type == ActionType.SCROLL:
                self._do_scroll(processed_config)
            elif action_type == ActionType.TYPE_TEXT:
                self._do_type_text(processed_config)
            elif action_type == ActionType.HOTKEY:
                self._do_hotkey(processed_config)
            elif action_type == ActionType.KEY_PRESS:
                self._do_key_press(processed_config)
            elif action_type == ActionType.WAIT:
                self._do_wait(processed_config)
            elif action_type == ActionType.IMAGE_CLICK:
                success = self._do_image_click(processed_config)
                if not success:
                    return False
            elif action_type == ActionType.IMAGE_WAIT:
                success = self._do_image_wait(processed_config)
                if not success:
                    return False
            elif action_type == ActionType.IMAGE_EXISTS:
                self._do_image_exists(processed_config)
            elif action_type == ActionType.SCREENSHOT:
                self._do_screenshot(processed_config)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
            
            # Delay after action
            delay_after = self.speed_controller.adjust_delay(action.delay_after)
            if delay_after > 0:
                time.sleep(delay_after)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing action {index}: {e}")
            if self._execution_log:
                self._execution_log.error_action_type = action.action_type.value
            return False
    
    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process config and replace variables."""
        processed = {}
        for key, value in config.items():
            if isinstance(value, str):
                processed[key] = replace_variables(value, self.variables)
            elif isinstance(value, dict):
                processed[key] = self._process_config(value)
            elif isinstance(value, list):
                processed[key] = [
                    replace_variables(v, self.variables) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                processed[key] = value
        return processed
    
    # ==================== MOUSE ACTIONS ====================
    
    def _do_click(self, config: Dict[str, Any]) -> None:
        """Perform a click action."""
        x = config.get('x')
        y = config.get('y')
        button = config.get('button', 'left')
        
        duration = self.speed_controller.get_mouse_duration()
        pyautogui.click(x, y, button=button, duration=duration)
        logger.debug(f"Click at ({x}, {y}) with {button} button")
    
    def _do_double_click(self, config: Dict[str, Any]) -> None:
        """Perform a double click action."""
        x = config.get('x')
        y = config.get('y')
        
        duration = self.speed_controller.get_mouse_duration()
        pyautogui.doubleClick(x, y, duration=duration)
        logger.debug(f"Double click at ({x}, {y})")
    
    def _do_right_click(self, config: Dict[str, Any]) -> None:
        """Perform a right click action."""
        x = config.get('x')
        y = config.get('y')
        
        duration = self.speed_controller.get_mouse_duration()
        pyautogui.rightClick(x, y, duration=duration)
        logger.debug(f"Right click at ({x}, {y})")
    
    def _do_move_to(self, config: Dict[str, Any]) -> None:
        """Move mouse to position."""
        x = config.get('x')
        y = config.get('y')
        
        duration = self.speed_controller.get_mouse_duration()
        pyautogui.moveTo(x, y, duration=duration)
        logger.debug(f"Move to ({x}, {y})")
    
    def _do_scroll(self, config: Dict[str, Any]) -> None:
        """Perform a scroll action."""
        x = config.get('x')
        y = config.get('y')
        scroll_amount = config.get('scroll_amount', 0)
        
        pyautogui.scroll(scroll_amount, x, y)
        logger.debug(f"Scroll {scroll_amount} at ({x}, {y})")
    
    # ==================== KEYBOARD ACTIONS ====================
    
    def _do_type_text(self, config: Dict[str, Any]) -> None:
        """Type text."""
        text = config.get('text', '')
        
        if not text:
            return
        
        interval = self.speed_controller.get_typing_speed()
        pyautogui.write(text, interval=interval)
        logger.debug(f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def _do_hotkey(self, config: Dict[str, Any]) -> None:
        """Execute a hotkey combination."""
        keys = config.get('keys', [])
        
        if not keys:
            return
        
        pyautogui.hotkey(*keys)
        logger.debug(f"Hotkey: {'+'.join(keys)}")
    
    def _do_key_press(self, config: Dict[str, Any]) -> None:
        """Press and release a key."""
        key = config.get('key')
        
        if key:
            pyautogui.press(key)
            logger.debug(f"Key press: {key}")
    
    # ==================== WAIT ACTIONS ====================
    
    def _do_wait(self, config: Dict[str, Any]) -> None:
        """Wait for specified duration."""
        duration = config.get('duration', 1.0)
        adjusted_duration = self.speed_controller.get_wait_time(duration)
        
        logger.debug(f"Wait {adjusted_duration:.2f}s (original: {duration}s)")
        time.sleep(adjusted_duration)
    
    # ==================== IMAGE ACTIONS ====================
    
    def _do_image_click(self, config: Dict[str, Any]) -> bool:
        """Click on an image found on screen."""
        image_path = config.get('image_path')
        confidence = config.get('confidence', 0.9)
        button = config.get('button', 'left')
        clicks = config.get('clicks', 1)
        
        if not image_path:
            logger.error("No image path provided for image_click")
            return False
        
        result = self.image_recognition.find_image(image_path, confidence)
        
        if result:
            x, y, w, h = result
            duration = self.speed_controller.get_mouse_duration()
            pyautogui.click(x, y, clicks=clicks, button=button, duration=duration)
            logger.debug(f"Image click at ({x}, {y})")
            return True
        else:
            logger.error(f"Image not found: {image_path}")
            return False
    
    def _do_image_wait(self, config: Dict[str, Any]) -> bool:
        """Wait for an image to appear on screen."""
        image_path = config.get('image_path')
        confidence = config.get('confidence', 0.9)
        timeout = config.get('timeout', 10.0)
        
        if not image_path:
            logger.error("No image path provided for image_wait")
            return False
        
        result = self.image_recognition.wait_for_image(
            image_path, 
            timeout=timeout,
            confidence=confidence
        )
        
        if result:
            logger.debug(f"Image appeared: {image_path}")
            return True
        else:
            logger.error(f"Image wait timeout: {image_path}")
            return False
    
    def _do_image_exists(self, config: Dict[str, Any]) -> bool:
        """Check if image exists on screen."""
        image_path = config.get('image_path')
        confidence = config.get('confidence', 0.9)
        
        if not image_path:
            return False
        
        exists = self.image_recognition.image_exists(image_path, confidence)
        logger.debug(f"Image exists: {exists}")
        return exists
    
    # ==================== SCREEN ACTIONS ====================
    
    def _do_screenshot(self, config: Dict[str, Any]) -> None:
        """Take a screenshot."""
        filename = config.get('filename', f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        region = config.get('region')  # (x, y, width, height)
        
        screenshot_path = config.get('screenshot_path', str(Path(config.screenshot_path if hasattr(config, 'screenshot_path') else 'data/screenshots')))
        
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        filepath = Path(screenshot_path) / f"{filename}.png"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        screenshot.save(filepath)
        
        logger.debug(f"Screenshot saved: {filepath}")
