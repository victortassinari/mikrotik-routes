import sys
import winreg
import os
from app.services.logger_service import logger

class StartupService:
    def __init__(self, app_name="MikroTikRoutes"):
        self.app_name = app_name
        self.key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_exe(self):
        """Check if running as a frozen executable."""
        return getattr(sys, 'frozen', False)

    def is_enabled(self):
        """Check if startup registry key exists for this app."""
        if not self.is_exe():
            return False
            
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, self.app_name)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking startup status: {e}")
            return False

    def set_enabled(self, enabled: bool):
        """Enable or disable startup registry key."""
        if not self.is_exe():
            logger.warning("Startup modification ignored: Not running as executable.")
            return False

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_WRITE) as key:
                if enabled:
                    exe_path = sys.executable
                    winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
                    logger.info(f"Added startup key for {exe_path}")
                else:
                    try:
                        winreg.DeleteValue(key, self.app_name)
                        logger.info("Removed startup key")
                    except FileNotFoundError:
                        pass # Already deleted
            return True
        except Exception as e:
            logger.error(f"Error changing startup status: {e}")
            return False
