import json
import os
import keyring
from typing import Optional, Dict

class ConfigManager:
    SERVICE_NAME = "MikrotikRoutes"
    CONFIG_FILE = "config.json"

    def __init__(self):
        self.config_data = self._load_config()

    def _load_config(self) -> Dict:
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config_data, f, indent=4)

    def get_last_host(self) -> str:
        return self.config_data.get('last_host', '')

    def set_last_host(self, host: str):
        self.config_data['last_host'] = host
        self.save_config()

    def get_last_user(self) -> str:
        return self.config_data.get('last_user', '')

    def set_last_user(self, user: str):
        self.config_data['last_user'] = user
        self.save_config()

    def get_remember_creds(self) -> bool:
        return self.config_data.get('remember_creds', False)

    def set_remember_creds(self, remember: bool):
        self.config_data['remember_creds'] = remember
        self.save_config()
        
    def get_remember_pass(self) -> bool:
        return self.config_data.get('remember_pass', False)

    def set_remember_pass(self, remember: bool):
        self.config_data['remember_pass'] = remember
        self.save_config()

    def get_use_ssl(self) -> bool:
        return self.config_data.get('use_ssl', False)

    def set_use_ssl(self, use_ssl: bool):
        self.config_data['use_ssl'] = use_ssl
        self.save_config()

    def save_password(self, host: str, user: str, password: str):
        username_key = f"{user}@{host}"
        try:
            keyring.set_password(self.SERVICE_NAME, username_key, password)
        except Exception as e:
            print(f"Error saving password to keyring: {e}")

    def get_password(self, host: str, user: str) -> Optional[str]:
        username_key = f"{user}@{host}"
        try:
            return keyring.get_password(self.SERVICE_NAME, username_key)
        except Exception as e:
            print(f"Error getting password from keyring: {e}")
            return None

    def delete_password(self, host: str, user: str):
        username_key = f"{user}@{host}"
        try:
            pass_exists = keyring.get_password(self.SERVICE_NAME, username_key)
            if pass_exists:
                keyring.delete_password(self.SERVICE_NAME, username_key)
        except Exception as e:
            print(f"Error deleting password from keyring: {e}")
