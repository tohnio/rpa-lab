"""
Image recognition module for RPA Lab.
Uses OpenCV for template matching to find images on screen.
"""
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image
import pyautogui
from loguru import logger

from src.utils.config import config


class ImageRecognition:
    """
    Image recognition using OpenCV template matching.
    """
    
    def __init__(self):
        self.default_confidence = config.image_confidence
        self.grayscale = config.get('image_recognition.grayscale', True)
        self.screen_width, self.screen_height = pyautogui.size()
    
    def find_image(
        self,
        template_path: str,
        confidence: Optional[float] = None,
        grayscale: Optional[bool] = None,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Find an image on the screen.
        
        Args:
            template_path: Path to the template image to find
            confidence: Matching confidence threshold (0.0 to 1.0)
            grayscale: Whether to use grayscale matching
            region: Screen region to search (x, y, width, height)
        
        Returns:
            Tuple of (x, y, width, height) of found location, or None if not found
        """
        confidence = confidence or self.default_confidence
        grayscale = grayscale if grayscale is not None else self.grayscale
        
        try:
            # Load template image
            template = cv2.imread(str(template_path))
            if template is None:
                logger.error(f"Failed to load template image: {template_path}")
                return None
            
            # Capture screen
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to OpenCV format
            screen_np = np.array(screenshot)
            screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale if needed
            if grayscale:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            else:
                template_gray = template
                screen_gray = screen_bgr
            
            # Template matching
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # Get template dimensions
                template_h, template_w = template_gray.shape[:2]
                
                # Calculate center point
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                # Add region offset if searching within a region
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                logger.debug(f"Found image at ({center_x}, {center_y}) with confidence {max_val:.2f}")
                return (center_x, center_y, template_w, template_h)
            
            logger.debug(f"Image not found. Best confidence: {max_val:.2f}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding image: {e}")
            return None
    
    def find_all_images(
        self,
        template_path: str,
        confidence: Optional[float] = None,
        grayscale: Optional[bool] = None,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> List[Tuple[int, int, int, int]]:
        """
        Find all occurrences of an image on the screen.
        
        Returns:
            List of tuples (x, y, width, height) for each found location
        """
        confidence = confidence or self.default_confidence
        grayscale = grayscale if grayscale is not None else self.grayscale
        
        try:
            template = cv2.imread(str(template_path))
            if template is None:
                logger.error(f"Failed to load template image: {template_path}")
                return []
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screen_np = np.array(screenshot)
            screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            
            if grayscale:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            else:
                template_gray = template
                screen_gray = screen_bgr
            
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            template_h, template_w = template_gray.shape[:2]
            locations = []
            
            # Find all matches above threshold
            threshold = confidence
            locs = np.where(result >= threshold)
            
            for pt in zip(*locs[::-1]):
                center_x = pt[0] + template_w // 2
                center_y = pt[1] + template_h // 2
                
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                locations.append((center_x, center_y, template_w, template_h))
            
            logger.debug(f"Found {len(locations)} image matches")
            return locations
            
        except Exception as e:
            logger.error(f"Error finding all images: {e}")
            return []
    
    def wait_for_image(
        self,
        template_path: str,
        timeout: float = 10.0,
        confidence: Optional[float] = None,
        check_interval: float = 0.5
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Wait for an image to appear on screen.
        
        Args:
            template_path: Path to the template image
            timeout: Maximum time to wait in seconds
            confidence: Matching confidence threshold
            check_interval: Time between checks in seconds
        
        Returns:
            Tuple of (x, y, width, height) if found, None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.find_image(template_path, confidence)
            if result:
                return result
            time.sleep(check_interval)
        
        logger.warning(f"Timeout waiting for image: {template_path}")
        return None
    
    def image_exists(
        self,
        template_path: str,
        confidence: Optional[float] = None
    ) -> bool:
        """Check if an image exists on screen."""
        return self.find_image(template_path, confidence) is not None
    
    def click_image(
        self,
        template_path: str,
        confidence: Optional[float] = None,
        button: str = 'left',
        clicks: int = 1,
        offset_x: int = 0,
        offset_y: int = 0
    ) -> bool:
        """
        Click on an image found on screen.
        
        Args:
            template_path: Path to the template image
            confidence: Matching confidence threshold
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            offset_x: X offset from center
            offset_y: Y offset from center
        
        Returns:
            True if image was found and clicked, False otherwise
        """
        result = self.find_image(template_path, confidence)
        if result:
            x, y, w, h = result
            click_x = x + offset_x
            click_y = y + offset_y
            
            pyautogui.click(click_x, click_y, clicks=clicks, button=button)
            logger.info(f"Clicked on image at ({click_x}, {click_y})")
            return True
        
        return False
    
    def get_image_center(self, template_path: str) -> Optional[Tuple[int, int]]:
        """Get the center coordinates of a template image file."""
        try:
            template = cv2.imread(str(template_path))
            if template is None:
                return None
            
            h, w = template.shape[:2]
            return (w // 2, h // 2)
        except:
            return None
    
    def highlight_image(
        self,
        template_path: str,
        confidence: Optional[float] = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> Optional[np.ndarray]:
        """
        Find an image and return a screenshot with it highlighted.
        
        Returns:
            Screenshot with highlighted region, or None if not found
        """
        result = self.find_image(template_path, confidence)
        if result:
            x, y, w, h = result
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            
            # Draw rectangle
            top_left = (x - w // 2, y - h // 2)
            bottom_right = (x + w // 2, y + h // 2)
            cv2.rectangle(screen_bgr, top_left, bottom_right, color, thickness)
            
            return screen_bgr
        
        return None


class ImageCapture:
    """
    Utility for capturing and saving screen regions as templates.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.screenshot_path
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Image.Image:
        """Capture a specific screen region."""
        return pyautogui.screenshot(region=(x, y, width, height))
    
    def capture_around_mouse(
        self,
        width: int = 100,
        height: int = 100
    ) -> Image.Image:
        """Capture a region around the mouse cursor."""
        mx, my = pyautogui.position()
        
        x = max(0, mx - width // 2)
        y = max(0, my - height // 2)
        
        # Adjust if region extends beyond screen
        screen_width, screen_height = pyautogui.size()
        if x + width > screen_width:
            x = screen_width - width
        if y + height > screen_height:
            y = screen_height - height
        
        return self.capture_region(x, y, width, height)
    
    def save_template(
        self,
        image: Image.Image,
        name: str
    ) -> Path:
        """Save an image as a template file."""
        filepath = self.output_dir / f"{name}.png"
        image.save(filepath, 'PNG')
        logger.info(f"Saved template: {filepath}")
        return filepath
    
    def capture_and_save(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        name: str
    ) -> Path:
        """Capture a region and save as template."""
        image = self.capture_region(x, y, width, height)
        return self.save_template(image, name)