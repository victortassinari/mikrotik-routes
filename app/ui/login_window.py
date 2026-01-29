import customtkinter as ctk
from app.config import settings
from app.utils.config_manager import ConfigManager

class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.config_manager = ConfigManager()
        
        self.title("MikroTik Login")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(fg_color=settings.COLORS["bg"])
        
        self._setup_ui()
        self._load_saved_data()
        
    def _setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 20), padx=20)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="LOGIN", 
                                        font=("Segoe UI", 24, "bold"), text_color=settings.COLORS["text"])
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(self.header_frame, text="Entre com as credenciais do MikroTik", 
                                           font=("Segoe UI", 12), text_color=settings.COLORS["text_dim"])
        self.subtitle_label.pack(pady=(5, 0))
        
        # Form
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(pady=20, padx=40, fill="x")
        
        # Host
        self.host_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Endereço IP / Host", height=40)
        self.host_entry.pack(pady=(0, 15), fill="x")
        
        # User
        self.user_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Usuário", height=40)
        self.user_entry.pack(pady=(0, 15), fill="x")
        
        # Password
        self.pass_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Senha", show="*", height=40)
        self.pass_entry.pack(pady=(0, 15), fill="x")
        
        # Checkboxes
        self.remember_creds_var = ctk.BooleanVar()
        self.remember_creds_chk = ctk.CTkCheckBox(self.form_frame, text="Lembrar Host e Usuário", 
                                                  variable=self.remember_creds_var,
                                                  text_color=settings.COLORS["text_dim"],
                                                  hover_color=settings.COLORS["accent"],
                                                  fg_color=settings.COLORS["success"])
        self.remember_creds_chk.pack(pady=(0, 10), anchor="w")
        
        self.remember_pass_var = ctk.BooleanVar()
        self.remember_pass_chk = ctk.CTkCheckBox(self.form_frame, text="Lembrar Senha (Seguro)", 
                                                 variable=self.remember_pass_var,
                                                 text_color=settings.COLORS["text_dim"],
                                                  hover_color=settings.COLORS["accent"],
                                                  fg_color=settings.COLORS["success"])
        self.remember_pass_chk.pack(pady=(0, 10), anchor="w")
        
        self.use_ssl_var = ctk.BooleanVar()
        self.use_ssl_chk = ctk.CTkCheckBox(self.form_frame, text="Usar Conexão Segura (SSL/HTTPS)", 
                                                 variable=self.use_ssl_var,
                                                 text_color=settings.COLORS["text_dim"],
                                                  hover_color=settings.COLORS["accent"],
                                                  fg_color=settings.COLORS["success"])
        self.use_ssl_chk.pack(pady=(0, 20), anchor="w")
        
        # Buttons
        self.login_btn = ctk.CTkButton(self, text="CONECTAR", 
                                      fg_color=settings.COLORS["success"], hover_color="#219150",
                                      font=("Segoe UI", 12, "bold"), height=45, corner_radius=10,
                                      command=self._attempt_login)
        self.login_btn.pack(pady=(0, 10), padx=40, fill="x")
        
        self.error_label = ctk.CTkLabel(self, text="", text_color=settings.COLORS["danger"], font=("Segoe UI", 11))
        self.error_label.pack(pady=(10, 0))

    def _load_saved_data(self):
        saved_host = self.config_manager.get_last_host()
        saved_user = self.config_manager.get_last_user()
        remember_creds = self.config_manager.get_remember_creds()
        remember_pass = self.config_manager.get_remember_pass()
        
        self.remember_creds_var.set(remember_creds)
        self.remember_pass_var.set(remember_pass)
        self.use_ssl_var.set(self.config_manager.get_use_ssl())
        
        if remember_creds:
            if saved_host: self.host_entry.insert(0, saved_host)
            if saved_user: self.user_entry.insert(0, saved_user)
            
            if remember_pass and saved_host and saved_user:
                saved_pass = self.config_manager.get_password(saved_host, saved_user)
                if saved_pass:
                    self.pass_entry.insert(0, saved_pass)

    def _attempt_login(self):
        host = self.host_entry.get().strip()
        user = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not host or not user:
            self.error_label.configure(text="Preencha Host e Usuário")
            return
            
        # Save preferences
        remember_creds = self.remember_creds_var.get()
        remember_pass = self.remember_pass_var.get()
        
        self.config_manager.set_remember_creds(remember_creds)
        self.config_manager.set_remember_pass(remember_pass)
        self.config_manager.set_use_ssl(self.use_ssl_var.get())
        
        if remember_creds:
            self.config_manager.set_last_host(host)
            self.config_manager.set_last_user(user)
        else:
            self.config_manager.set_last_host('')
            self.config_manager.set_last_user('')
            
        if remember_pass and remember_creds:
            self.config_manager.save_password(host, user, password)
        else:
            self.config_manager.delete_password(host, user)
            
        # Proceed
        self.on_login_success(host, user, password, self.use_ssl_var.get())
        self.destroy()
