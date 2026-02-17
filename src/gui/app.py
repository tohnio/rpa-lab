"""
Main application class for RPA Lab GUI.
"""
import customtkinter as ctk
from typing import Optional
from loguru import logger

from src.gui.main_window import MainWindow
from src.utils.config import config
from src.database.db_manager import db
from src.core.scheduler import task_scheduler


class App:
    """
    Main application class that initializes and runs the RPA Lab GUI.
    """
    
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode(config.theme)
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title(config.app_name)
        
        # Set window size
        window_width = config.get('ui.window_width', 1200)
        window_height = config.get('ui.window_height', 800)
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(800, 600)
        
        # Create main window content
        self.main_window = MainWindow(self.root, self)
        self.main_window.pack(fill="both", expand=True)
        
        # Setup close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize database
        config.ensure_directories()
        
        logger.info(f"{config.app_name} v{config.app_version} initialized")
    
    def run(self) -> None:
        """Start the application main loop."""
        self.root.mainloop()
    
    def on_closing(self) -> None:
        """Handle application closing."""
        logger.info("Application closing")
        
        # Stop scheduler
        if task_scheduler.is_running:
            task_scheduler.stop()
        
        # Destroy window
        self.root.destroy()
    
    def show_info(self, title: str, message: str) -> None:
        """Show info dialog."""
        self.root.after(0, lambda: self._show_dialog("info", title, message))
    
    def show_error(self, title: str, message: str) -> None:
        """Show error dialog."""
        self.root.after(0, lambda: self._show_dialog("error", title, message))
    
    def show_warning(self, title: str, message: str) -> None:
        """Show warning dialog."""
        self.root.after(0, lambda: self._show_dialog("warning", title, message))
    
    def _show_dialog(self, dialog_type: str, title: str, message: str) -> None:
        """Internal method to show dialog on main thread."""
        if dialog_type == "error":
            dialog = ctk.CTkInputDialog(text=message, title=title)
        else:
            # Create a simple message box
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(title)
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center on parent
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # Message
            label = ctk.CTkLabel(dialog, text=message, wraplength=350)
            label.pack(pady=20, padx=20)
            
            # OK button
            btn = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
            btn.pack(pady=10)
    
    def set_theme(self, theme: str) -> None:
        """Set application theme."""
        ctk.set_appearance_mode(theme)
        config.set('app.theme', theme)
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark theme."""
        current = config.theme
        new_theme = "light" if current == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme