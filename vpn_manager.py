# vpn_manager.py
"""
VPN management for Telethon Unlimited Login
"""
import os
import json
import logging
import random
import subprocess
from datetime import datetime

logger = logging.getLogger("telethon_login.vpn_manager")

class VPNManager:
    def __init__(self, database):
        """Initialize VPN manager"""
        self.db = database
        
    def setup_vpn(self, vpn_type="cloudflare"):
        """Setup VPN configuration for an account"""
        try:
            if vpn_type == "cloudflare":
                return self._setup_cloudflare()
            else:
                logger.warning(f"Tipe VPN {vpn_type} tidak didukung, menggunakan Cloudflare")
                return self._setup_cloudflare()
                
        except Exception as e:
            logger.error(f"Error saat setup VPN: {str(e)}")
            return None
            
    def _setup_cloudflare(self):
        """Setup Cloudflare 1.1.1.1 proxy"""
        # Cloudflare DNS servers
        cf_dns = ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"]
        
        # Create VPN config with a randomly selected Cloudflare DNS
        config = {
            "type": "cloudflare",
            "proxy": {
                "proxy_type": "http", 
                "addr": random.choice(cf_dns),
                "port": 80,
                "rdns": True
            },
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Cloudflare VPN setup dengan server {config['proxy']['addr']}")
        return config
        
    def get_proxy_from_config(self, vpn_config):
        """Get proxy settings from VPN config"""
        try:
            # If string, parse it as JSON
            if isinstance(vpn_config, str):
                vpn_config = json.loads(vpn_config)
                
            # Get proxy from config
            if vpn_config and "proxy" in vpn_config:
                proxy_config = vpn_config["proxy"]
                
                # Return in format expected by Telethon
                return (
                    proxy_config.get("proxy_type", "http"),
                    proxy_config.get("addr", "1.1.1.1"),
                    proxy_config.get("port", 80),
                    proxy_config.get("rdns", True)
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error saat mendapatkan proxy dari config: {str(e)}")
            return None
            
    def check_vpn_connectivity(self, vpn_config):
        """Check connectivity to VPN server"""
        try:
            # If string, parse it as JSON
            if isinstance(vpn_config, str):
                vpn_config = json.loads(vpn_config)
                
            if not vpn_config or "proxy" not in vpn_config:
                return False
                
            # Get address to ping
            addr = vpn_config["proxy"].get("addr", "1.1.1.1")
            
            # Try to ping
            try:
                # Use different commands for different OS
                if os.name == 'nt':  # Windows
                    ping_command = ["ping", "-n", "1", "-w", "1000", addr]
                else:  # Linux/Mac
                    ping_command = ["ping", "-c", "1", "-W", "1", addr]
                    
                # Run ping command
                result = subprocess.run(
                    ping_command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                
                # Check result
                if result.returncode == 0:
                    logger.info(f"Koneksi ke VPN {addr} berhasil")
                    return True
                else:
                    logger.warning(f"Koneksi ke VPN {addr} gagal")
                    return False
                    
            except Exception as e:
                logger.error(f"Error saat ping VPN {addr}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error saat mengecek konektivitas VPN: {str(e)}")
            return False
            
    def rotate_vpn(self, account_phone):
        """Rotate VPN for an account"""
        try:
            # Get account
            account = self.db.get_account(account_phone)
            if not account:
                logger.error(f"Akun dengan nomor {account_phone} tidak ditemukan")
                return False
                
            # Setup new VPN
            vpn_config = self.setup_vpn()
            if not vpn_config:
                logger.error(f"Gagal setup VPN baru untuk {account_phone}")
                return False
                
            # Update VPN in database
            vpn_config_str = json.dumps(vpn_config)
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE accounts SET vpn_config = ? WHERE phone = ?",
                (vpn_config_str, account_phone)
            )
            
            # Add log entry
            cursor.execute('''
            INSERT INTO logs (phone, action, status, details)
            VALUES (?, ?, ?, ?)
            ''', (account_phone, "rotate_vpn", "success", f"New VPN: {vpn_config['proxy']['addr']}"))
            
            self.db.conn.commit()
            logger.info(f"VPN untuk akun {account_phone} berhasil dirotasi")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat merotasi VPN untuk akun {account_phone}: {str(e)}")
            return False
