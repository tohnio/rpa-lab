# Core Package
"""
Core automation modules for RPA Lab.
"""
from src.core.recorder import Recorder
from src.core.player import Player
from src.core.image_recognition import ImageRecognition
from src.core.speed_controller import SpeedController

__all__ = ['Recorder', 'Player', 'ImageRecognition', 'SpeedController']