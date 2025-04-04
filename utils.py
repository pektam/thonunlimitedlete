# utils.py
"""
Utility functions for Telethon Unlimited Login
"""
import os
import re
import logging
import shutil
from datetime import datetime

logger = logging.getLogger("telethon_login.utils")

def setup_folders():
    """Setup required folders for the system"""
    folders = ["accounts", "sessions", "logs", "backup"]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Folder {folder} dibuat")
            
    # Create empty failed.txt in logs if it doesn't exist
    if not os.path.exists("logs/failed.txt"):
        with open("logs/failed.txt", "w") as f:
            f.write("# Log untuk akun yang gagal login\n")
            
    logger.info("Setup folder selesai")
    
def format_phone(phone):
    """Format phone number to standard format (+62xxx)"""
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Check if number starts with 0, replace with +62
    if phone_digits.startswith('0'):
        phone_digits = "62" + phone_digits[1:]
        
    # Check if number starts with 62 but without +
    if phone_digits.startswith('62') and not phone.startswith('+'):
        return f"+{phone_digits}"
        
    # If not starting with +, add it
    if not phone.startswith('+'):
        return f"+{phone_digits}"
        
    return phone
    
def validate_phone_number(phone):
    """Validate phone number format"""
    # Basic validation: must start with + followed by digits
    if not re.match(r'^\+\d{10,15}$', phone):
        return False
        
    # For Indonesian numbers: must start with +62
    if phone.startswith('+62') and len(phone) >= 10 and len(phone) <= 15:
        return True
        
    # Could add more country-specific validation here
    
    return True
    
def clean_old_logs(max_age_days=30):
    """Clean log files older than specified days"""
    try:
        current_time = datetime.now()
        log_dir = "logs"
        
        if not os.path.exists(log_dir):
            return
            
        for file in os.listdir(log_dir):
            if file == "failed.txt":
                continue  # Skip main failed log
                
            file_path = os.path.join(log_dir, file)
            
            # Check if file is older than max_age_days
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_days = (current_time - file_time).days
            
            if age_days > max_age_days:
                os.remove(file_path)
                logger.info(f"File log lama dihapus: {file}")
                
        logger.info("Pembersihan log lama selesai")
        
    except Exception as e:
        logger.error(f"Error saat membersihkan log lama: {str(e)}")
        
def clean_old_backups(max_backups=10):
    """Keep only the most recent backups"""
    try:
        backup_dir = "backup"
        
        if not os.path.exists(backup_dir):
            return
            
        # Get all backup directories
        backups = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                backups.append({
                    'path': item_path,
                    'time': os.path.getmtime(item_path)
                })
                
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x['time'], reverse=True)
        
        # Remove old backups
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                shutil.rmtree(backup['path'])
                logger.info(f"Backup lama dihapus: {backup['path']}")
                
        logger.info("Pembersihan backup lama selesai")
        
    except Exception as e:
        logger.error(f"Error saat membersihkan backup lama: {str(e)}")
        
def auto_maintenance():
    """Perform automatic maintenance tasks"""
    try:
        # Clean old logs
        clean_old_logs()
        
        # Clean old backups
        clean_old_backups()
        
        logger.info("Pemeliharaan otomatis selesai")
        
    except Exception as e:
        logger.error(f"Error saat melakukan pemeliharaan otomatis: {str(e)}")
