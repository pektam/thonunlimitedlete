# database.py
"""
Database operations for Telethon Unlimited Login
"""
import os
import json
import sqlite3
import logging
import shutil
from datetime import datetime

logger = logging.getLogger("telethon_login.database")

class Database:
    def __init__(self, db_path="accounts/accounts.db"):
        """Initialize database connection"""
        self.db_path = db_path
        
        # Create accounts directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_database()
        
    def init_database(self):
        """Initialize database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Create accounts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            api_id INTEGER,
            api_hash TEXT,
            username TEXT,
            status TEXT,
            additional_info TEXT,
            vpn_config TEXT,
            is_used INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            last_check TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            action TEXT,
            status TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
        
    def add_account(self, phone, api_id, api_hash, status="new", username=None, additional_info=None, vpn_config=None):
        """Add a new account to the database"""
        try:
            cursor = self.conn.cursor()
            
            # Convert vpn_config to JSON string if provided
            if vpn_config and isinstance(vpn_config, dict):
                vpn_config = json.dumps(vpn_config)
                
            # Check if account already exists
            cursor.execute("SELECT id FROM accounts WHERE phone = ?", (phone,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing account
                cursor.execute('''
                UPDATE accounts SET 
                    api_id = ?, 
                    api_hash = ?, 
                    username = ?,
                    status = ?,
                    additional_info = ?,
                    vpn_config = ?,
                    last_check = CURRENT_TIMESTAMP
                WHERE phone = ?
                ''', (api_id, api_hash, username, status, additional_info, vpn_config, phone))
            else:
                # Insert new account
                cursor.execute('''
                INSERT INTO accounts 
                    (phone, api_id, api_hash, username, status, additional_info, vpn_config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (phone, api_id, api_hash, username, status, additional_info, vpn_config))
            
            # Add log entry
            cursor.execute('''
            INSERT INTO logs (phone, action, status, details)
            VALUES (?, ?, ?, ?)
            ''', (phone, "add_account", status, f"API: {api_id}"))
            
            self.conn.commit()
            logger.info(f"Akun {phone} berhasil {'diperbarui' if existing else 'ditambahkan'} ke database")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat menambahkan akun {phone}: {str(e)}")
            return False
            
    def get_account(self, phone):
        """Get account info from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE phone = ?", (phone,))
            account = cursor.fetchone()
            
            if not account:
                return None
                
            # Convert to dict
            account_dict = dict(account)
            
            # Parse VPN config if it exists
            if account_dict.get('vpn_config'):
                try:
                    account_dict['vpn_config'] = json.loads(account_dict['vpn_config'])
                except:
                    pass
                    
            return account_dict
            
        except Exception as e:
            logger.error(f"Error saat mengambil data akun {phone}: {str(e)}")
            return None
            
    def account_exists(self, phone):
        """Check if account exists in database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE phone = ?", (phone,))
            return cursor.fetchone() is not None
            
        except Exception as e:
            logger.error(f"Error saat mengecek keberadaan akun {phone}: {str(e)}")
            return False
            
    def update_account_status(self, phone, status, additional_info=None, last_check=None):
        """Update account status in database"""
        try:
            cursor = self.conn.cursor()
            
            params = [status, phone]
            query = "UPDATE accounts SET status = ?"
            
            if additional_info is not None:
                query += ", additional_info = ?"
                params.insert(1, additional_info)
                
            if last_check is not None:
                query += ", last_check = ?"
                params.insert(1 if additional_info is None else 2, last_check)
                
            query += " WHERE phone = ?"
            
            cursor.execute(query, params)
            
            # Add log entry
            cursor.execute('''
            INSERT INTO logs (phone, action, status, details)
            VALUES (?, ?, ?, ?)
            ''', (phone, "update_status", status, additional_info or ""))
            
            self.conn.commit()
            logger.info(f"Status akun {phone} diperbarui menjadi {status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat memperbarui status akun {phone}: {str(e)}")
            return False
            
    def mark_account_used(self, phone, is_used=True):
        """Mark account as used/idle"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE accounts SET 
                is_used = ?,
                last_used = CURRENT_TIMESTAMP
            WHERE phone = ?
            ''', (1 if is_used else 0, phone))
            
            self.conn.commit()
            logger.info(f"Akun {phone} ditandai sebagai {'digunakan' if is_used else 'idle'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat menandai penggunaan akun {phone}: {str(e)}")
            return False
            
    def get_all_accounts(self, status=None):
        """Get all accounts, optionally filtered by status"""
        try:
            cursor = self.conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM accounts WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
                
            accounts = cursor.fetchall()
            
            # Convert to list of dicts
            result = []
            for account in accounts:
                account_dict = dict(account)
                
                # Parse VPN config if it exists
                if account_dict.get('vpn_config'):
                    try:
                        account_dict['vpn_config'] = json.loads(account_dict['vpn_config'])
                    except:
                        pass
                        
                result.append(account_dict)
                
            return result
            
        except Exception as e:
            logger.error(f"Error saat mengambil daftar akun: {str(e)}")
            return []
            
    def delete_account(self, phone):
        """Delete account from database"""
        try:
            cursor = self.conn.cursor()
            
            # Add log entry before deleting
            cursor.execute('''
            INSERT INTO logs (phone, action, status, details)
            VALUES (?, ?, ?, ?)
            ''', (phone, "delete_account", "deleted", "Account deleted from database"))
            
            # Delete account
            cursor.execute("DELETE FROM accounts WHERE phone = ?", (phone,))
            
            self.conn.commit()
            logger.info(f"Akun {phone} dihapus dari database")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saat menghapus akun {phone}: {str(e)}")
            return False
            
    def get_account_logs(self, phone, limit=10):
        """Get logs for specific account"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT * FROM logs 
            WHERE phone = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            ''', (phone, limit))
            
            logs = cursor.fetchall()
            return [dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error saat mengambil log untuk akun {phone}: {str(e)}")
            return []
            
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def backup_database(self, backup_path):
        """Create a backup of the database"""
        try:
            # Close connection to avoid locks
            self.conn.close()
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Reopen connection
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            logger.info(f"Database berhasil di-backup ke {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saat melakukan backup database: {str(e)}")
            # Try to reopen connection if failed
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except:
                pass
            return False
