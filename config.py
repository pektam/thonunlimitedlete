# config.py
"""
Configuration settings for Telethon Unlimited Login
"""
import os
import json

class Config:
    def __init__(self, config_file="config.json"):
        """Initialize configuration, load from file or set defaults"""
        self.config_file = config_file
        
        # Default values
        self.DEFAULT_API_ID = 12345  # Ganti dengan API_ID Anda
        self.DEFAULT_API_HASH = "0123456789abcdef0123456789abcdef"  # Ganti dengan API_HASH Anda
        self.DEFAULT_2FA_PASSWORD = "Dgvt61zwe@"  # Password 2FA default
        self.ADMIN_NOTIFICATION_ID = None  # ID Telegram untuk notifikasi
        self.DEFAULT_VPN = "cloudflare"  # Default VPN (cloudflare)
        
        # Load config if exists
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    
                # Update values from config file
                self.DEFAULT_API_ID = config.get("api_id", self.DEFAULT_API_ID)
                self.DEFAULT_API_HASH = config.get("api_hash", self.DEFAULT_API_HASH)
                self.DEFAULT_2FA_PASSWORD = config.get("2fa_password", self.DEFAULT_2FA_PASSWORD)
                self.ADMIN_NOTIFICATION_ID = config.get("admin_notification_id", self.ADMIN_NOTIFICATION_ID)
                self.DEFAULT_VPN = config.get("default_vpn", self.DEFAULT_VPN)
                
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            # Create default config file
            self.save_config()
            
    def save_config(self):
        """Save configuration to file"""
        config = {
            "api_id": self.DEFAULT_API_ID,
            "api_hash": self.DEFAULT_API_HASH,
            "2fa_password": self.DEFAULT_2FA_PASSWORD,
            "admin_notification_id": self.ADMIN_NOTIFICATION_ID,
            "default_vpn": self.DEFAULT_VPN
        }
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
