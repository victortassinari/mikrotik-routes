import urllib.request
import socket

class NetworkService:
    @staticmethod
    def get_public_ip():
        """Busca o IP público via ipify.org ou icanhazip.com."""
        services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ifconfig.me/ip"
        ]
        
        for service in services:
            try:
                # Timeout agressivo para falhar rápido e tentar o próximo
                with urllib.request.urlopen(service, timeout=1) as response:
                    return response.read().decode('utf-8').strip()
            except Exception:
                continue
                
        return "Erro (Offline?)"
