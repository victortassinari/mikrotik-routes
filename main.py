import customtkinter as ctk
from app.config import settings
from app.ui.main_window import MainWindow
from app.ui.login_window import LoginWindow
from app.services.logger_service import logger

def main():
    ctk.set_appearance_mode(settings.APPEARANCE_MODE)
    ctk.set_default_color_theme(settings.DEFAULT_COLOR_THEME)
    
    # Store credentials from login
    auth_data = {}
    
    def on_login(host, user, password, use_ssl):
        auth_data['host'] = host
        auth_data['user'] = user
        auth_data['password'] = password
        auth_data['use_ssl'] = use_ssl
    
    # Show Login
    login_app = LoginWindow(on_login_success=on_login)
    login_app.mainloop()
    
    # If login was successful (auth_data is populated), show Main Window
    if auth_data:
        app = MainWindow(host=auth_data['host'], 
                        user=auth_data['user'], 
                        password=auth_data['password'],
                        use_ssl=auth_data['use_ssl'])
        app.mainloop()

if __name__ == "__main__":
    main()
