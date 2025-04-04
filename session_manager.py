# session_manager.py
"""
Session management for Telethon Unlimited Login
"""
import os
import logging
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    FloodWaitError,
    UserDeactivatedBanError,
    AuthKeyUnregisteredError
)

logger = logging.getLogger("telethon_login.session_manager")

class SessionManager:
    def __init__(self, database):
        """Initialize session manager"""
        self.db = database
        self.active_clients = {}
        
        # Create sessions directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)
        
    async def initialize_client(self, phone, api_id=None, api_hash=None, proxy=None):
        """Initialize a Telethon client for the given phone number"""
        try:
            # Get account info if not provided
            if not api_id or not api_hash:
                account = self.db.get_account(phone)
                if not account:
                    logger.error(f"Akun untuk {phone} tidak ditemukan dalam database")
                    return None
                    
                api_id = account['api_id']
                api_hash = account['api_hash']
                
                # Setup proxy if configured in account
                if not proxy and account.get('vpn_config'):
                    from vpn_manager import VPNManager
                    vpn_manager = VPNManager(self.db)
                    proxy = vpn_manager.get_proxy_from_config(account['vpn_config'])
                    
            # Create session path
            session_path = f"sessions/{phone}"
            
            # Initialize client
            client = TelegramClient(
                session_path,
                api_id,
                api_hash,
                proxy=proxy
            )
            
            # Connect client
            await client.connect()
            
            # Check if client is connected
            if await client.is_user_authorized():
                logger.info(f"Client untuk {phone} berhasil diinisialisasi dan terautentikasi")
                self.active_clients[phone] = client
                return client
            else:
                logger.warning(f"Client untuk {phone} tidak terautentikasi")
                await client.disconnect()
                return None
                
        except UserDeactivatedBanError:
            logger.error(f"Akun {phone} telah dibanned")
            self.db.update_account_status(phone, "banned")
            return None
            
        except AuthKeyUnregisteredError:
            logger.error(f"Session untuk {phone} telah expired")
            self.db.update_account_status(phone, "expired")
            return None
            
        except Exception as e:
            logger.error(f"Error saat menginisialisasi client untuk {phone}: {str(e)}")
            return None
            
    async def get_client(self, phone):
        """Get or create a client for the given phone number"""
        if phone in self.active_clients:
            return self.active_clients[phone]
            
        return await self.initialize_client(phone)
        
    async def check_session(self, phone):
        """Check if a session is still valid"""
        client = await self.get_client(phone)
        
        if not client:
            logger.warning(f"Tidak dapat mendapatkan client untuk {phone}")
            return False
            
        try:
            if await client.is_user_authorized():
                # Update account last check
                self.db.update_account_status(
                    phone=phone, 
                    status="active", 
                    last_check=datetime.now()
                )
                logger.info(f"Session untuk {phone} valid")
                return True
            else:
                logger.warning(f"Session untuk {phone} tidak terautentikasi")
                self.db.update_account_status(phone, "unauthorized")
                return False
                
        except Exception as e:
            logger.error(f"Error saat mengecek session {phone}: {str(e)}")
            return False
            
    async def relogin_account(self, phone, verification_code=None, password=None):
        """Attempt to relogin an account"""
        try:
            # Get account info
            account = self.db.get_account(phone)
            if not account:
                logger.error(f"Akun untuk {phone} tidak ditemukan dalam database")
                return False, "Akun tidak ditemukan"
                
            api_id = account['api_id']
            api_hash = account['api_hash']
            
            # Setup proxy if configured
            proxy = None
            if account.get('vpn_config'):
                from vpn_manager import VPNManager
                vpn_manager = VPNManager(self.db)
                proxy = vpn_manager.get_proxy_from_config(account['vpn_config'])
                
            # Create session path
            session_path = f"sessions/{phone}"
            
            # Check if session file exists and rename it if it does
            if os.path.exists(f"{session_path}.session"):
                backup_name = f"{session_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.session.bak"
                os.rename(f"{session_path}.session", backup_name)
                logger.info(f"Session file for {phone} backed up to {backup_name}")
                
            # Initialize client
            client = TelegramClient(
                session_path,
                api_id,
                api_hash,
                proxy=proxy
            )
            
            await client.connect()
            
            # Send code request if verification code not provided
            if not verification_code:
                await client.send_code_request(phone)
                logger.info(f"Kode verifikasi dikirim ke {phone}")
                await client.disconnect()
                return False, "Kode verifikasi dikirim"
                
            try:
                # Try to sign in with code
                await client.sign_in(phone, verification_code)
            except SessionPasswordNeededError:
                # 2FA is enabled
                if not password:
                    # Use default password from config
                    from config import Config
                    config = Config()
                    password = config.DEFAULT_2FA_PASSWORD
                    
                # Try to sign in with password
                await client.sign_in(password=password)
                
            # Check if login successful
            if await client.is_user_authorized():
                # Update account status
                self.db.update_account_status(
                    phone=phone, 
                    status="active", 
                    last_check=datetime.now()
                )
                
                # Store in active clients
                self.active_clients[phone] = client
                
                logger.info(f"Relogin berhasil untuk {phone}")
                return True, "Relogin berhasil"
            else:
                await client.disconnect()
                logger.error(f"Relogin gagal untuk {phone}")
                return False, "Relogin gagal"
                
        except PhoneCodeInvalidError:
            logger.error(f"Kode verifikasi tidak valid untuk {phone}")
            self.db.update_account_status(phone, "code_error")
            return False, "Kode verifikasi tidak valid"
            
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.error(f"FloodWaitError untuk {phone}: tunggu {wait_time} detik")
            self.db.update_account_status(
                phone=phone, 
                status="flood_wait",
                additional_info=f"wait:{wait_time}"
            )
            return False, f"Flood wait error: tunggu {wait_time} detik"
            
        except Exception as e:
            logger.error(f"Error saat relogin akun {phone}: {str(e)}")
            self.db.update_account_status(
                phone=phone, 
                status="error",
                additional_info=str(e)
            )
            return False, f"Error: {str(e)}"
            
    async def close_all_clients(self):
        """Close all active clients"""
        for phone, client in self.active_clients.items():
            try:
                await client.disconnect()
                logger.info(f"Client untuk {phone} ditutup")
            except Exception as e:
                logger.error(f"Error saat menutup client {phone}: {str(e)}")
                
        self.active_clients = {}
        
    async def recover_session(self, phone):
        """Try to recover a broken session"""
        try:
            # Rename broken session file
            session_path = f"sessions/{phone}.session"
            if os.path.exists(session_path):
                backup_name = f"sessions/{phone}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.session.bak"
                os.rename(session_path, backup_name)
                logger.info(f"Session file untuk {phone} di-backup ke {backup_name}")
                
            # Update account status
            self.db.update_account_status(
                phone=phone, 
                status="recovery_needed",
                additional_info="Session file backed up, needs relogin"
            )
            
            return True, "Session di-backup, perlu relogin"
            
        except Exception as e:
            logger.error(f"Error saat mencoba recovery session {phone}: {str(e)}")
            return False, f"Error: {str(e)}"
            
    def __del__(self):
        """Ensure all clients are disconnected"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.close_all_clients())
