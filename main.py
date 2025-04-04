# main.py
"""
Telethon Unlimited Login
Sistem manajemen multiple akun Telegram menggunakan Telethon
"""
import os
import sys
import logging
import argparse
import asyncio
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError, 
    PhoneCodeInvalidError, 
    SessionPasswordNeededError,
    FloodWaitError,
    UserDeactivatedBanError,
    AuthKeyUnregisteredError
)

from config import Config
from database import Database
from session_manager import SessionManager
from utils import setup_folders, format_phone, validate_phone_number
from vpn_manager import VPNManager
from monitor import Monitor

# Setup logging
logger = logging.getLogger("telethon_login")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler(f"logs/telethon_login_{datetime.now().strftime('%Y%m%d')}.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class TelethonUnlimitedLogin:
    def __init__(self):
        """Initialize the Telethon Unlimited Login system"""
        setup_folders()
        self.config = Config()
        self.db = Database()
        self.session_manager = SessionManager(self.db)
        self.vpn_manager = VPNManager(self.db)
        self.monitor = Monitor(self.config.ADMIN_NOTIFICATION_ID)
        logger.info("Telethon Unlimited Login initialized")
        
    async def add_account(self, phone, api_id=None, api_hash=None, use_vpn=False):
        """Add a new Telegram account"""
        try:
            # Validate phone number
            phone = format_phone(phone)
            if not validate_phone_number(phone):
                logger.error(f"Nomor telepon tidak valid: {phone}")
                return False, "Nomor telepon tidak valid"
                
            # Check if phone already exists
            if self.db.account_exists(phone):
                logger.warning(f"Akun dengan nomor {phone} sudah ada dalam database")
                return False, "Akun sudah ada dalam database"
                
            # Use default API credentials if not provided
            if not api_id or not api_hash:
                api_id = self.config.DEFAULT_API_ID
                api_hash = self.config.DEFAULT_API_HASH
                
            # Create session name
            session_name = f"sessions/{phone}"
            
            # Setup VPN if requested
            if use_vpn:
                vpn_config = self.vpn_manager.setup_vpn()
                proxy = vpn_config.get('proxy')
            else:
                proxy = None
                vpn_config = None
                
            # Initialize client
            client = TelegramClient(
                session_name, 
                api_id, 
                api_hash,
                proxy=proxy
            )
            
            await client.connect()
            
            # Check if already authorized
            if await client.is_user_authorized():
                # Save to database with active status
                self.db.add_account(
                    phone=phone, 
                    api_id=api_id, 
                    api_hash=api_hash, 
                    status="active",
                    vpn_config=vpn_config
                )
                logger.info(f"Akun {phone} sudah terautentikasi, disimpan ke database")
                await client.disconnect()
                return True, "Akun sudah terautentikasi dan disimpan"
                
            # Start authorization process
            try:
                code = await client.send_code_request(phone)
                logger.info(f"Kode verifikasi dikirim ke {phone}")
                
                # Get verification code from user
                verification_code = input(f"Masukkan kode verifikasi untuk {phone}: ")
                
                # Sign in with code
                try:
                    await client.sign_in(phone, verification_code)
                except SessionPasswordNeededError:
                    # 2FA enabled, use default password
                    logger.info(f"2FA dibutuhkan untuk {phone}, menggunakan password default")
                    await client.sign_in(password=self.config.DEFAULT_2FA_PASSWORD)
                
                # Check if login successful
                if await client.is_user_authorized():
                    # Get additional account info
                    me = await client.get_me()
                    username = me.username if me.username else ""
                    
                    # Save to database
                    self.db.add_account(
                        phone=phone, 
                        api_id=api_id, 
                        api_hash=api_hash, 
                        status="active",
                        username=username,
                        vpn_config=vpn_config
                    )
                    
                    logger.info(f"Akun {phone} berhasil login dan disimpan ke database")
                    # Send notification
                    await self.monitor.send_notification(f"✅ Akun baru berhasil ditambahkan: {phone}")
                    
                    await client.disconnect()
                    return True, "Akun berhasil ditambahkan"
                else:
                    logger.error(f"Gagal login untuk {phone} setelah autentikasi")
                    await client.disconnect()
                    return False, "Gagal login setelah autentikasi"
                    
            except PhoneCodeInvalidError:
                logger.error(f"Kode verifikasi tidak valid untuk {phone}")
                await client.disconnect()
                self.db.add_account(
                    phone=phone, 
                    api_id=api_id, 
                    api_hash=api_hash, 
                    status="code_error"
                )
                return False, "Kode verifikasi tidak valid"
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.error(f"FloodWaitError untuk {phone}: tunggu {wait_time} detik")
                await client.disconnect()
                self.db.add_account(
                    phone=phone, 
                    api_id=api_id, 
                    api_hash=api_hash, 
                    status="flood_wait",
                    additional_info=f"wait:{wait_time}"
                )
                return False, f"Flood wait error: tunggu {wait_time} detik"
                
        except PhoneNumberInvalidError:
            logger.error(f"Nomor telepon tidak valid: {phone}")
            return False, "Nomor telepon tidak valid"
            
        except Exception as e:
            logger.error(f"Error saat menambahkan akun {phone}: {str(e)}")
            # Log to failed.txt
            with open("logs/failed.txt", "a") as f:
                f.write(f"{datetime.now()} - {phone} - {str(e)}\n")
            return False, f"Error: {str(e)}"
            
    async def check_account(self, phone):
        """Check if an account is still valid"""
        try:
            # Get account from database
            account = self.db.get_account(phone)
            if not account:
                logger.error(f"Akun dengan nomor {phone} tidak ditemukan")
                return False, "Akun tidak ditemukan"
                
            # Get session and API info
            session_name = f"sessions/{phone}"
            api_id = account['api_id']
            api_hash = account['api_hash']
            
            # Setup VPN if configured
            proxy = None
            if account.get('vpn_config'):
                proxy = self.vpn_manager.get_proxy_from_config(account['vpn_config'])
                
            # Initialize client
            client = TelegramClient(
                session_name, 
                api_id, 
                api_hash,
                proxy=proxy
            )
            
            await client.connect()
            
            # Check if authorized
            if await client.is_user_authorized():
                # Update last_check in database
                self.db.update_account_status(phone, "active", last_check=datetime.now())
                logger.info(f"Akun {phone} valid dan aktif")
                await client.disconnect()
                return True, "Akun valid dan aktif"
            else:
                # Update status in database
                self.db.update_account_status(phone, "unauthorized")
                logger.warning(f"Akun {phone} tidak terautentikasi")
                await client.disconnect()
                return False, "Akun tidak terautentikasi"
                
        except UserDeactivatedBanError:
            # Account is banned
            self.db.update_account_status(phone, "banned")
            logger.error(f"Akun {phone} telah dibanned")
            return False, "Akun telah dibanned"
            
        except AuthKeyUnregisteredError:
            # Session expired
            self.db.update_account_status(phone, "expired")
            logger.error(f"Session untuk akun {phone} telah expired")
            return False, "Session telah expired"
            
        except Exception as e:
            logger.error(f"Error saat mengecek akun {phone}: {str(e)}")
            self.db.update_account_status(phone, "error", additional_info=str(e))
            return False, f"Error: {str(e)}"
            
    async def check_all_accounts(self):
        """Check all accounts in the database"""
        accounts = self.db.get_all_accounts()
        
        results = {
            "active": 0,
            "error": 0,
            "banned": 0,
            "expired": 0,
            "other": 0
        }
        
        for account in accounts:
            phone = account['phone']
            logger.info(f"Mengecek akun {phone}")
            
            success, message = await self.check_account(phone)
            account_status = self.db.get_account(phone)['status']
            
            if account_status in results:
                results[account_status] += 1
            else:
                results["other"] += 1
                
        # Log summary
        logger.info(f"Check semua akun selesai: {results}")
        return results
        
    async def delete_account(self, phone):
        """Delete an account from database and remove session file"""
        try:
            # Check if account exists
            if not self.db.account_exists(phone):
                logger.error(f"Akun dengan nomor {phone} tidak ditemukan")
                return False, "Akun tidak ditemukan"
                
            # Delete from database
            self.db.delete_account(phone)
            
            # Remove session file
            session_file = f"sessions/{phone}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
                logger.info(f"File session untuk {phone} dihapus")
                
            logger.info(f"Akun {phone} berhasil dihapus")
            return True, "Akun berhasil dihapus"
            
        except Exception as e:
            logger.error(f"Error saat menghapus akun {phone}: {str(e)}")
            return False, f"Error: {str(e)}"
            
    async def backup_system(self):
        """Backup database and session files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create backup directory
            backup_dir = f"backup/{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup database
            self.db.backup_database(f"{backup_dir}/accounts.db")
            
            # Backup session files
            os.makedirs(f"{backup_dir}/sessions", exist_ok=True)
            for file in os.listdir("sessions"):
                if file.endswith(".session"):
                    os.system(f"cp sessions/{file} {backup_dir}/sessions/")
                    
            logger.info(f"Backup sistem berhasil dibuat di {backup_dir}")
            return True, f"Backup berhasil dibuat di {backup_dir}"
            
        except Exception as e:
            logger.error(f"Error saat melakukan backup: {str(e)}")
            return False, f"Error: {str(e)}"

    async def run_cli(self):
        """Run CLI interface"""
        from cli import run_cli
        await run_cli(self)


# Command-line interface
async def main():
    parser = argparse.ArgumentParser(description="Telethon Unlimited Login")
    parser.add_argument("--check-all", action="store_true", help="Cek semua akun")
    parser.add_argument("--backup", action="store_true", help="Backup sistem")
    parser.add_argument("--add", help="Tambah akun baru (nomor telepon)")
    parser.add_argument("--check", help="Cek akun (nomor telepon)")
    parser.add_argument("--delete", help="Hapus akun (nomor telepon)")
    parser.add_argument("--list", action="store_true", help="Tampilkan semua akun")
    parser.add_argument("--cli", action="store_true", help="Jalankan CLI interaktif")
    
    args = parser.parse_args()
    
    tul = TelethonUnlimitedLogin()
    
    if args.add:
        success, message = await tul.add_account(args.add)
        print(message)
        
    elif args.check:
        success, message = await tul.check_account(args.check)
        print(message)
        
    elif args.delete:
        success, message = await tul.delete_account(args.delete)
        print(message)
        
    elif args.check_all:
        results = await tul.check_all_accounts()
        print(f"Hasil pengecekan: {results}")
        
    elif args.backup:
        success, message = await tul.backup_system()
        print(message)
        
    elif args.list:
        accounts = tul.db.get_all_accounts()
        print(f"Total akun: {len(accounts)}")
        for account in accounts:
            print(f"Phone: {account['phone']} | Status: {account['status']} | Last Check: {account.get('last_check', 'Belum pernah')}")
            
    elif args.cli:
        await tul.run_cli()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
