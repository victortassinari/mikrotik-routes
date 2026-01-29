import customtkinter as ctk
import threading
from app.config import settings
from app.services.mikrotik_service import MikrotikService
from app.services.network_service import NetworkService
from app.services.startup_service import StartupService
import pystray
from pystray import MenuItem as item
import os
import time
import sys
from PIL import Image, ImageDraw, ImageTk
from tkinter import messagebox
from app.services.path_service import get_resource_path
from app.services.logger_service import logger

class MainWindow(ctk.CTk):
    def __init__(self, host, user, password, use_ssl=False):
        super().__init__()
        self.mikrotik = MikrotikService(host, user, password, use_ssl)
        self.network = NetworkService()
        self.startup_service = StartupService()
        
        self.title("MikroTik Link Dashboard")
        self.resizable(False, False)
        self.configure(fg_color=settings.COLORS["bg"])

        # Icon configuration
        self.icon_path = get_resource_path(os.path.join("app", "assets", "icon.png"))
        if os.path.exists(self.icon_path):
            try:
                self.icon_image = Image.open(self.icon_path)
                self.tk_icon = ImageTk.PhotoImage(self.icon_image.resize((32, 32)))
                self.after(200, lambda: self.iconphoto(False, self.tk_icon))
            except Exception as e:
                logger.error(f"Could not set window icon: {e}")
                self.icon_image = None
        else:
            self.icon_image = None

        self.links = []
        self.link_buttons = {} # Dict for easy access: comment -> button
        self.ping_labels = {}  # Dict for ping labels: comment -> label
        self._status_updating = False # Lock for status loop
        self.btn_auto = None
        self.last_update_time = "--:--:--"
        
        # Load Warning Icon
        self.warning_path = get_resource_path(os.path.join("app", "assets", "warning.png"))
        if os.path.exists(self.warning_path):
            self.warning_image = ctk.CTkImage(light_image=Image.open(self.warning_path), size=(20, 20))
        else:
            self.warning_image = None

        self._setup_ui()
        self.discover_links()

    def _setup_ui(self):
        # Header section
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 20), padx=20, fill="x")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="LINK DASHBOARD", 
                                        font=("Segoe UI", 20, "bold"), text_color=settings.COLORS["text"])
        self.title_label.pack(side="left")
        
        # Refresh button in header
        self.refresh_btn = ctk.CTkButton(self.header_frame, text="↻", width=30, height=30,
                                        fg_color="transparent", hover_color=settings.COLORS["card"],
                                        text_color=settings.COLORS["text_dim"], 
                                        font=("Segoe UI", 18),
                                        command=self.discover_links)
        self.refresh_btn.pack(side="left", padx=(10, 0))
        
        self.version_label = ctk.CTkLabel(self.header_frame, text="v2.1", 
                                          font=("Segoe UI", 12), text_color=settings.COLORS["text_dim"])
        self.version_label.pack(side="right", pady=(10, 0))

        # Status Card
        self.status_card = ctk.CTkFrame(self, fg_color=settings.COLORS["card"], corner_radius=15)
        self.status_card.pack(pady=10, padx=25, fill="x")
        self.status_card.grid_columnconfigure(0, weight=1)
        
        # Link Ativo
        self.active_link_title = ctk.CTkLabel(self.status_card, text="CONEXÃO ATUAL", 
                                             font=("Segoe UI", 10, "bold"), text_color=settings.COLORS["text_dim"])
        self.active_link_title.grid(row=0, column=0, pady=(15, 0), padx=20, sticky="w")
        
        self.active_link_label = ctk.CTkLabel(self.status_card, text="Carregando...", 
                                             font=("Segoe UI", 18, "bold"), text_color=settings.COLORS["text"],
                                             compound="right", padx=10)
        self.active_link_label.grid(row=1, column=0, pady=(0, 10), padx=20, sticky="w")
        
        # Divider
        self.divider = ctk.CTkFrame(self.status_card, height=2, fg_color=settings.COLORS["accent"])
        self.divider.grid(row=2, column=0, padx=20, sticky="ew")
        
        # Info Row (Mode & IP)
        self.info_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.info_frame.grid(row=3, column=0, pady=15, padx=20, sticky="ew")
        self.info_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Modo Column
        self.mode_container = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.mode_container.grid(row=0, column=0, sticky="nw")
        
        self.mode_title = ctk.CTkLabel(self.mode_container, text="MODO OPERAÇÃO", 
                                       font=("Segoe UI", 9, "bold"), text_color=settings.COLORS["text_dim"])
        self.mode_title.pack(anchor="w")
        
        self.mode_label = ctk.CTkLabel(self.mode_container, text="--", 
                                       font=("Segoe UI", 13, "bold"))
        self.mode_label.pack(anchor="w")
        
        # IP Column
        self.ip_container = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.ip_container.grid(row=0, column=1, sticky="ne")
        
        self.ip_title = ctk.CTkLabel(self.ip_container, text="IP PÚBLICO", 
                                    font=("Segoe UI", 9, "bold"), text_color=settings.COLORS["text_dim"])
        self.ip_title.pack(anchor="e")
        
        self.ip_label = ctk.CTkLabel(self.ip_container, text="0.0.0.0", 
                                    font=("Segoe UI", 13, "bold"), text_color=settings.COLORS["text"])
        self.ip_label.pack(anchor="e")

        # Control Section
        self.control_label = ctk.CTkLabel(self, text="SELECIONAR LINK MANUAL", 
                                         font=("Segoe UI", 11, "bold"), text_color=settings.COLORS["text_dim"])
        self.control_label.pack(pady=(25, 10), padx=30, anchor="w")

        # Buttons Grid
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=0, padx=25, fill="x")
        
        self.discovery_label = ctk.CTkLabel(self.btn_frame, text="Buscando links no MikroTik...", font=("Segoe UI", 12, "italic"))
        self.discovery_label.pack(pady=10)

        # Failover Button
        self.failover_container = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.failover_container.pack(pady=(20, 25), padx=30, fill="x")
        self.failover_container.pack_propagate(False)

        self.btn_auto = ctk.CTkButton(self.failover_container, text="ATIVAR FAILOVER AUTOMÁTICO", 
                                     fg_color=settings.COLORS["success"], hover_color="#219150",
                                     font=("Segoe UI", 12, "bold"), height=50, corner_radius=10,
                                     command=self.enable_all_links)
        
        # Settings Section (Startup)
        if self.startup_service.is_exe():
            self.settings_container = ctk.CTkFrame(self, fg_color="transparent")
            self.settings_container.pack(pady=(5, 15), padx=35, fill="x")
            
            self.startup_var = ctk.BooleanVar(value=self.startup_service.is_enabled())
            self.startup_chk = ctk.CTkCheckBox(self.settings_container, text="Iniciar junto com o Windows", 
                                             font=("Segoe UI", 12), text_color=settings.COLORS["text"],
                                             command=self.toggle_startup,
                                             variable=self.startup_var,
                                             onvalue=True, offvalue=False,
                                             checkbox_height=18, checkbox_width=18, border_width=2,
                                             hover_color=settings.COLORS["success"], fg_color=settings.COLORS["success"])
            self.startup_chk.pack(anchor="w")
        
        # Loading Indicator
        self.loading_container = ctk.CTkFrame(self, fg_color="transparent")
        
        self.loading_msg = ctk.CTkLabel(self.loading_container, text="⏳ AGUARDE: TROCANDO LINK E VERIFICANDO CONEXÃO...", 
                                        font=("Segoe UI", 10, "bold"), text_color=settings.COLORS["success"])
        self.loading_msg.pack(pady=(0, 5))
        
        self.loading_bar = ctk.CTkProgressBar(self.loading_container, mode="indeterminate", height=6, 
                                             fg_color=settings.COLORS["accent"], progress_color=settings.COLORS["success"])
        self.loading_bar.pack(fill="x", padx=10)

        # Footer Status
        self.last_update_label = ctk.CTkLabel(self, text="Carregando status...", 
                                             font=("Segoe UI", 10), text_color=settings.COLORS["text_dim"])
        self.last_update_label.pack(pady=(15, 5), side="bottom")

        # Move tray setup and protocol to the end of init or here
        self._create_tray_icon()
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def discover_links(self):
        threading.Thread(target=self._do_discovery, daemon=True).start()

    def _do_discovery(self):
        try:
            self.links = self.mikrotik.discover_links()
            self.after(0, self._create_dynamic_ui)
        except Exception as e:
            logger.error(f"UI Discovery Error: {e}")
            self.after(0, lambda: self.discovery_label.configure(text="Erro ao conectar no MikroTik", text_color="red"))

    def _create_dynamic_ui(self):
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
        
        if not self.links:
            self.discovery_label = ctk.CTkLabel(self.btn_frame, text="Nenhum link com 'Link' no comentário encontrado.", font=("Segoe UI", 12))
            self.discovery_label.pack(pady=10)
            return

        num_cols = min(len(self.links), 3)
        for i in range(num_cols):
            self.btn_frame.grid_columnconfigure(i, weight=1)

        self.link_buttons = {}
        self.ping_labels = {}
        for i, link in enumerate(self.links):
            # Container for Button + Ping
            container = ctk.CTkFrame(self.btn_frame, fg_color="transparent")
            row = i // 3
            col = i % 3
            container.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            container.grid_columnconfigure(0, weight=1)

            btn = ctk.CTkButton(container, text=link['label'], height=45, corner_radius=10,
                               command=lambda c=link['comment']: self.switch_link(c))
            btn.grid(row=0, column=0, sticky="ew")
            
            ping_lbl = ctk.CTkLabel(container, text="-- ms", font=("Segoe UI", 9), text_color=settings.COLORS["text_dim"])
            ping_lbl.grid(row=1, column=0, pady=(2, 0))
            
            self.link_buttons[link['comment']] = btn
            self.ping_labels[link['comment']] = ping_lbl
        
        self.update_status()
        self.after(200, self._adjust_window_size)

    def _adjust_window_size(self):
        self.update_idletasks()
        width = 450
        height = self.winfo_reqheight()
        self.geometry(f"{width}x{height}")

    def set_loading(self, is_loading):
        if is_loading:
            for btn in self.link_buttons.values():
                btn.configure(state="disabled")
            if self.btn_auto: self.btn_auto.configure(state="disabled")
            self.loading_container.pack(pady=(15, 10), padx=35, fill="x")
            self.loading_bar.start()
        else:
            # We don't restore button states here because _update_ui_status 
            # will do it properly based on which links are active/reachable
            self.loading_bar.stop()
            self.loading_container.pack_forget()
        self.after(10, self._adjust_window_size)

    def switch_link(self, target_comment):
        self.set_loading(True)
        # Visual feedback on the button itself
        if target_comment in self.link_buttons:
            self.link_buttons[target_comment].configure(text="Conectando...")
        threading.Thread(target=self._do_switch_link, args=(target_comment,), daemon=True).start()

    def _do_switch_link(self, target_comment):
        try:
            # Tenta o switch inicial
            try:
                self.mikrotik.switch_link(target_comment, self.links)
            except Exception as e:
                logger.error(f"Erro inicial ao trocar link: {e}")
                raise e

            # Verificar conectividade
            start_time = time.time()
            online = False
            
            # Tenta verificar o IP por X segundos
            while time.time() - start_time < settings.LINK_VERIFICATION_TIMEOUT:
                time.sleep(1) # Reduzido de 2s para 1s para ser mais responsivo
                try:
                    ip = self.network.get_public_ip()
                    if ip and "Erro" not in ip:
                        online = True
                        break
                except Exception:
                    continue 
            
            if not online:
                logger.warning(f"Link {target_comment} offline após switch. Ativando failover de emergência.")
                # Tenta reativar failover (com retry simples)
                for _ in range(2):
                    try:
                        self.mikrotik.enable_all_links(self.links)
                        break
                    except Exception as e:
                        logger.error(f"Erro ao reativar failover (tentativa): {e}")
                        time.sleep(1)
                
                self.after(0, lambda: messagebox.showwarning(
                    "Link Offline", 
                    f"O link selecionado não tem conectividade.\nFailover Automático foi reativado por segurança."
                ))
            
            self.after(0, self.update_status)
        except Exception as e:
            logger.error(f"UI Switch Link Error: {e}")
        finally:
            # Garante que SEMPRE sai do estado de loading
            self.after(0, lambda: self.set_loading(False))

    def enable_all_links(self):
        self.set_loading(True)
        threading.Thread(target=self._do_enable_all, daemon=True).start()

    def _do_enable_all(self):
        try:
            self.mikrotik.enable_all_links(self.links)
            self.after(settings.SWITCH_WAIT_TIME, self.update_status)
        except Exception as e:
            logger.error(f"UI Enable All Error: {e}")
            self.after(0, lambda: self.set_loading(False))

    def update_status(self):
        if self._status_updating:
            return
        self._status_updating = True
        threading.Thread(target=self._fetch_status, daemon=True).start()

    def _fetch_status(self):
        current_ip = self.network.get_public_ip()
        
        # Show intermediate "checking" state first for better UX
        # This prevents links from showing as offline while pings are in progress
        checking_pings = {link['comment']: 'checking' for link in self.links}
        self.after(0, lambda: self._update_ping_status(checking_pings))
        
        try:
            active_link, mode, unreachable_links, pings = self.mikrotik.get_status(self.links)
        except Exception as e:
            logger.error(f"UI Fetch Status Error: {e}")
            active_link = "Erro de Conexão"
            mode = "Erro"
            unreachable_links = []
            pings = {}

        self.after(0, lambda: self._update_ui_status(active_link, mode, current_ip, unreachable_links, pings))
    
    def _update_ping_status(self, pings):
        """Update only ping labels without touching other UI elements."""
        try:
            for comment, ping_lbl in self.ping_labels.items():
                val_raw = str(pings.get(comment, "--")).lower()
                
                if val_raw == "checking":
                    ping_lbl.configure(text="⏳", text_color=settings.COLORS["text_dim"])
                # Other states will be handled by full _update_ui_status
        except Exception as e:
            logger.error(f"Error in _update_ping_status: {e}")
        
    def toggle_startup(self):
        enabled = self.startup_var.get()
        success = self.startup_service.set_enabled(enabled)
        if not success:
            # Revert if failed
            self.startup_var.set(not enabled)
            messagebox.showerror("Erro", "Não foi possível alterar a configuração de inicialização.\nVerifique as permissões.")

    def _update_tray_menu(self, active_link, mode, unreachable_links):
        if not self.tray_icon:
            return

        menu_items = [
            item(f'Link: {active_link}', self.show_window, enabled=False),
            item(f'Status: {mode} ({self.last_update_time})', self.show_window, enabled=False),
            item('Forçar Atualização', lambda icon, item: self.discover_links()),
            pystray.Menu.SEPARATOR
        ]

        # Add link switching options
        for link in self.links:
            is_active = (link['label'] == active_link)
            is_unreachable = link['comment'] in unreachable_links
            
            menu_items.append(item(
                f"Ativar {link['label']}{' (Offline)' if is_unreachable else ''}", 
                (lambda l=link: lambda icon, item: self.switch_link(l['comment']))(),
                checked=lambda item, l=link: active_link == l['label'],
                enabled=not is_unreachable
            ))

        if mode == "Manual":
            menu_items.append(item('Ativar Failover Automático', lambda icon, item: self.enable_all_links()))
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            item('Abrir Dashboard', self.show_window, default=True),
            item('Sair', self.quit_app)
        ])

        self.tray_icon.menu = pystray.Menu(*menu_items)

    def _update_ui_status(self, active_link, mode, current_ip, unreachable_links, pings):
        try:
            # Update timestamp
            self.last_update_time = time.strftime("%H:%M:%S")
            if hasattr(self, 'last_update_label'):
                self.last_update_label.configure(text=f"Última atualização: {self.last_update_time}")

            self.active_link_label.configure(text=active_link)
            
            # Check if active link is unreachable
            is_active_down = any(l for l in self.links if l['label'] == active_link and l['comment'] in unreachable_links)
            if is_active_down:
                self.active_link_label.configure(text_color=settings.COLORS["danger"], image=self.warning_image)
            else:
                self.active_link_label.configure(text_color=settings.COLORS["text"], image=None)

            self.mode_label.configure(
                text=mode.upper(), 
                text_color=settings.COLORS["success"] if mode == "Failover Automático" else settings.COLORS["warning"] if mode == "Manual" else settings.COLORS["danger"]
            )
            
            if mode == "Manual":
                if self.btn_auto: 
                    self.btn_auto.pack(fill="both", expand=True)
                    self.btn_auto.configure(state="normal")
            else:
                if self.btn_auto: self.btn_auto.pack_forget()
                
            # Update Individual Link Buttons and Pings
            for comment, btn in self.link_buttons.items():
                link_data = next((l for l in self.links if l['comment'] == comment), None)
                is_active = (link_data and link_data['label'] == active_link)
                is_unreachable = comment in unreachable_links
                
                # Update Ping Label
                if comment in self.ping_labels:
                    val_raw = str(pings.get(comment, "--")).lower()
                    color = settings.COLORS["text_dim"]
                    
                    # Handle "checking" state - ping is still in progress
                    if val_raw == "checking":
                        val = "⏳"
                        color = settings.COLORS["text_dim"]
                    else:
                        ms_val = None
                        # Robust numeric check: extract digits and dots
                        clean_val = "".join(filter(lambda x: x.isdigit() or x == '.', val_raw))
                        
                        if clean_val:
                            try:
                                ms_val = float(clean_val)
                                # Format: no decimals if .0, else 1 decimal
                                if ms_val == int(ms_val):
                                    val = f"{int(ms_val)} ms"
                                else:
                                    val = f"{ms_val:.1f} ms"
                            except ValueError:
                                val = "-- ms"
                        elif val_raw in ["timeout", "err"]:
                            val = "-"
                            color = settings.COLORS["danger"]
                        else:
                            val = "-" # Default for unparseable strings

                        if ms_val is not None:
                            if ms_val > 200: color = settings.COLORS["danger"]
                            elif ms_val > 100: color = settings.COLORS["warning"]
                            else: color = settings.COLORS["success"]
                    
                    self.ping_labels[comment].configure(text=val, text_color=color)

                # Check if link is offline (unreachable OR failed ping)
                # Don't mark as offline if still checking
                ping_status = pings.get(comment, "")
                ping_failed = ping_status in ["err", "timeout"]
                is_checking = ping_status == "checking"
                is_offline = is_unreachable or (ping_failed and not is_checking)
                
                if is_offline:
                    btn.configure(
                        image=self.warning_image, 
                        state="disabled", 
                        fg_color=settings.COLORS["card"], 
                        text_color=settings.COLORS["text_dim"],
                        text=f"{link_data['label']} (Offline)"
                    )
                elif is_active:
                    btn.configure(
                        image=None, 
                        state="normal", 
                        fg_color=settings.COLORS["success"],
                        text=link_data['label']
                    )
                else:
                    btn.configure(
                        image=None, 
                        state="normal", 
                        fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                        text=link_data['label']
                    )

            self.ip_label.configure(text=current_ip)
            self.set_loading(False)
            self._update_tray_menu(active_link, mode, unreachable_links)
            self.after(100, self._adjust_window_size)
        except Exception as e:
            logger.error(f"Error in _update_ui_status: {e}")
        finally:
            self._status_updating = False
            # Ensure the refresh interval always triggers next update
            self.after(settings.REFRESH_INTERVAL, self.update_status)

    def hide_window(self):
        self.withdraw()
        if not self.tray_icon:
            self._create_tray_icon()

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self._actual_quit)

    def _actual_quit(self):
        try:
            self.quit()
            self.destroy()
        except:
            pass
        finally:
            sys.exit()

    def _create_tray_icon(self):
        def get_tray_image():
            if self.icon_image:
                return self.icon_image
            
            # Fallback to simple icon if file not found
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), settings.COLORS["bg"])
            dc = ImageDraw.Draw(image)
            dc.ellipse([5, 5, 59, 59], fill=settings.COLORS["success"])
            dc.line([(20, 45), (20, 20), (32, 35), (44, 20), (44, 45)], fill="white", width=5)
            return image

        # Initial simple menu
        menu = pystray.Menu(
            item('Carregando...', lambda: None, enabled=False),
            item('Sair', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("mikrotik_routes", get_tray_image(), "MikroTik Link Dashboard", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
