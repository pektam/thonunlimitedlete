# monitor.py
"""
Monitoring and notifications for Telethon Unlimited Login
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.errors import FloodWaitError

logger = logging.getLogger("telethon_login.monitor")

class Monitor:
    def __init__(self, admin_id=None, api_id=None, api_hash=None):
        """Initialize monitoring system"""
        self.admin_id = admin_id
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
        
        # Initialize from config if not provided
        if not api_id or not api_hash:
            from config import Config
            config = Config()
            
            if not self.admin_id:
                self.admin_id = config.ADMIN_NOTIFICATION_ID
                
            self.api_id = config.DEFAULT_API_ID
            self.api_hash = config.DEFAULT_API_HASH
            
    async def init_client(self):
        """Initialize notification client"""
        if not self.admin_id:
            logger.warning("ADMIN_NOTIFICATION_ID tidak diatur, notifikasi dinonaktifkan")
            return False
            
        try:
            # Create session directory if not exists
            os.makedirs("sessions", exist_ok=True)
            
            # Initialize client
            self.client = TelegramClient(
                "sessions/notification_client", 
                self.api_id, 
                self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("Client notifikasi tidak terautentikasi")
                return False
                
            logger.info("Client notifikasi berhasil diinisialisasi")
            return True
            
        except Exception as e:
            logger.error(f"Error saat inisialisasi client notifikasi: {str(e)}")
            return False
            
    async def send_notification(self, message):
        """Send notification to admin"""
        if not self.admin_id:
            return False
            
        try:
            if not self.client or not self.client.is_connected():
                success = await self.init_client()
                if not success:
                    return False
                    
            # Send message
            await self.client.send_message(
                self.admin_id,
                f"🤖 **Telethon Unlimited Login**\n\n{message}\n\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            logger.info(f"Notifikasi terkirim ke {self.admin_id}")
            return True
            
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.error(f"FloodWaitError saat mengirim notifikasi: tunggu {wait_time} detik")
            return False
            
        except Exception as e:
            logger.error(f"Error saat mengirim notifikasi: {str(e)}")
            return False
            
    async def monitor_accounts(self, database, session_manager):
        """Monitor accounts and send notifications for issues"""
        if not self.admin_id:
            return
            
        try:
            # Get all accounts
            accounts = database.get_all_accounts()
            
            # Counters
            total = len(accounts)
            active = 0
            banned = 0
            expired = 0
            error = 0
            other = 0
            
            # Check each account
            for account in accounts:
                phone = account['phone']
                status = account['status']
                
                # Update counters
                if status == "active":
                    active += 1
                elif status == "banned":
                    banned += 1
                elif status == "expired":
                    expired += 1
                elif status == "error":
                    error += 1
                else:
                    other += 1
                    
                # Check for accounts that haven't been checked in over 24 hours
                if account.get('last_check'):
                    last_check = datetime.fromisoformat(account['last_check'])
                    if datetime.now() - last_check > timedelta(hours=24):
                        # Check account
                        success, _ = await session_manager.check_session(phone)
                        if not success:
                            await self.send_notification(
                                f"⚠️ Akun {phone} perlu pengecekan manual.\n"
                                f"Status: {status}\n"
                                f"Last check: {last_check}"
                            )
                            
            # Send daily summary if we have accounts
            if total > 0:
                await self.send_notification(
                    f"📊 **Laporan Harian Akun**\n\n"
                    f"Total akun: {total}\n"
                    f"✅ Aktif: {active}\n"
                    f"❌ Banned: {banned}\n"
                    f"⏱️ Expired: {expired}\n"
                    f"⚠️ Error: {error}\n"
                    f"Other: {other}"
                )
                
        except Exception as e:
            logger.error(f"Error saat monitoring akun: {str(e)}")
            
    async def close(self):
        """Close notification client"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            logger.info("Client notifikasi ditutup")
