# cli.py
"""
Command Line Interface for Telethon Unlimited Login
"""
import os
import sys
import csv
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger("telethon_login.cli")

async def display_menu():
    """Display the main menu"""
    print("\n" + "=" * 50)
    print("TELETHON UNLIMITED LOGIN - MENU UTAMA")
    print("=" * 50)
    print("1. Tambah Akun")
    print("2. Tambah Multiple Akun (CSV)")
    print("3. Cek Akun")
    print("4. Cek Semua Akun")
    print("5. Lihat Semua Akun")
    print("6. Hapus Akun")
    print("7. Backup Sistem")
    print("8. Maintenance")
    print("9. Rotate VPN")
    print("0. Keluar")
    print("=" * 50)
    
    choice = input("Pilih menu (0-9): ")
    return choice
    
async def add_account(tul):
    """Add a new account"""
    print("\n" + "=" * 50)
    print("TAMBAH AKUN BARU")
    print("=" * 50)
    
    phone = input("Nomor telepon (+62xxx): ")
    use_vpn = input("Gunakan VPN? (y/n): ").lower() == 'y'
    
    print(f"Menambahkan akun {phone}...")
    success, message = await tul.add_account(phone, use_vpn=use_vpn)
    
    if success:
        print(f"✅ Sukses: {message}")
    else:
        print(f"❌ Gagal: {message}")
        
    input("Tekan Enter untuk kembali ke menu...")
    
async def add_multiple_accounts(tul):
    """Add multiple accounts from CSV file"""
    print("\n" + "=" * 50)
    print("TAMBAH MULTIPLE AKUN (CSV)")
    print("=" * 50)
    print("Format CSV: phone,use_vpn")
    print("Contoh: +628123456789,y")
    
    file_path = input("Path ke file CSV: ")
    
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} tidak ditemukan")
        input("Tekan Enter untuk kembali ke menu...")
        return
        
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            accounts = list(reader)
            
        print(f"Ditemukan {len(accounts)} akun dalam file CSV")
        print("Mulai proses penambahan akun...")
        
        results = {"success": 0, "failed": 0}
        
        for i, row in enumerate(accounts):
            if len(row) < 1:
                print(f"Baris {i+1}: Format tidak valid, dilewati")
                results["failed"] += 1
                continue
                
            phone = row[0].strip()
            use_vpn = len(row) > 1 and row[1].lower() in ('y', 'yes', 'true', '1')
            
            print(f"[{i+1}/{len(accounts)}] Menambahkan {phone}...")
            success, message = await tul.add_account(phone, use_vpn=use_vpn)
            
            if success:
                print(f"✅ {phone}: {message}")
                results["success"] += 1
            else:
                print(f"❌ {phone}: {message}")
                results["failed"] += 1
                
        print("\n" + "=" * 50)
        print(f"HASIL: Sukses {results['success']}, Gagal {results['failed']}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error saat membaca file CSV: {str(e)}")
        
    input("Tekan Enter untuk kembali ke menu...")
    
async def check_account(tul):
    """Check a specific account"""
    print("\n" + "=" * 50)
    print("CEK AKUN")
    print("=" * 50)
    
    phone = input("Nomor telepon (+62xxx): ")
    
    print(f"Mengecek akun {phone}...")
    success, message = await tul.check_account(phone)
    
    if success:
        print(f"✅ Sukses: {message}")
    else:
        print(f"❌ Gagal: {message}")
        
    # Show account details
    account = tul.db.get_account(phone)
    if account:
        print("\nDetail Akun:")
        print(f"Phone: {account['phone']}")
        print(f"Status: {account['status']}")
        print(f"Username: {account.get('username', 'N/A')}")
        print(f"Last Check: {account.get('last_check', 'Belum pernah')}")
        print(f"Last Used: {account.get('last_used', 'Belum pernah')}")
        print(f"Created At: {account.get('created_at', 'Unknown')}")
        
        # Show recent logs
        logs = tul.db.get_account_logs(phone, limit=5)
        if logs:
            print("\nRiwayat Aktivitas Terakhir:")
            for log in logs:
                print(f"{log['timestamp']} - {log['action']} ({log['status']})")
                
    input("Tekan Enter untuk kembali ke menu...")
    
async def check_all_accounts(tul):
    """Check all accounts"""
    print("\n" + "=" * 50)
    print("CEK SEMUA AKUN")
    print("=" * 50)
    
    print("Memulai pengecekan semua akun...")
    results = await tul.check_all_accounts()
    
    print("\nHasil Pengecekan:")
    print(f"✅ Aktif: {results['active']}")
    print(f"❌ Banned: {results['banned']}")
    print(f"⏱️ Expired: {results['expired']}")
    print(f"⚠️ Error: {results['error']}")
    print(f"Lainnya: {results['other']}")
    print(f"TOTAL: {sum(results.values())}")
    
    input("Tekan Enter untuk kembali ke menu...")
    
async def list_accounts(tul):
    """List all accounts"""
    print("\n" + "=" * 50)
    print("DAFTAR SEMUA AKUN")
    print("=" * 50)
    
    # Get filter options
    filter_option = input("Filter by status (kosongkan untuk semua): ")
    
    # Get accounts
    accounts = tul.db.get_all_accounts(filter_option if filter_option else None)
    
    # Display counts
    statuses = {}
    for account in accounts:
        status = account['status']
        if status in statuses:
            statuses[status] += 1
        else:
            statuses[status] = 1
            
    print(f"\nTotal akun: {len(accounts)}")
    for status, count in statuses.items():
        print(f"{status}: {count}")
        
    # Display accounts
    if accounts:
        print("\n{:<20} {:<15} {:<20} {:<10}".format("PHONE", "STATUS", "LAST CHECK", "USERNAME"))
        print("-" * 70)
        
        for account in accounts:
            last_check = account.get('last_check', 'Never')
            if last_check and last_check != 'Never':
                try:
                    last_check = datetime.fromisoformat(last_check).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
                    
            print("{:<20} {:<15} {:<20} {:<10}".format(
                account['phone'],
                account['status'],
                last_check,
                account.get('username', 'N/A')
            ))
    else:
        print("\nTidak ada akun yang ditemukan")
        
    input("\nTekan Enter untuk kembali ke menu...")
    
async def delete_account(tul):
    """Delete an account"""
    print("\n" + "=" * 50)
    print("HAPUS AKUN")
    print("=" * 50)
    
    phone = input("Nomor telepon (+62xxx): ")
    
    # Confirm deletion
    confirm = input(f"Yakin ingin menghapus akun {phone}? (y/n): ")
    if confirm.lower() != 'y':
        print("Penghapusan dibatalkan")
        input("Tekan Enter untuk kembali ke menu...")
        return
        
    print(f"Menghapus akun {phone}...")
    success, message = await tul.delete_account(phone)
    
    if success:
        print(f"✅ Sukses: {message}")
    else:
        print(f"❌ Gagal: {message}")
        
    input("Tekan Enter untuk kembali ke menu...")
    
async def backup_system(tul):
    """Backup the system"""
    print("\n" + "=" * 50)
    print("BACKUP SISTEM")
    print("=" * 50)
    
    print("Memulai backup sistem...")
    success, message = await tul.backup_system()
    
    if success:
        print(f"✅ Sukses: {message}")
    else:
        print(f"❌ Gagal: {message}")
        
    input("Tekan Enter untuk kembali ke menu...")
    
async def maintenance(tul):
    """Perform system maintenance"""
    print("\n" + "=" * 50)
    print("MAINTENANCE SISTEM")
    print("=" * 50)
    
    print("Memulai maintenance sistem...")
    
    # Clean old logs
    from utils import clean_old_logs, clean_old_backups
    print("Membersihkan log lama...")
    clean_old_logs()
    
    # Clean old backups
    print("Membersihkan backup lama...")
    clean_old_backups()
    
    # Backup system
    print("Membuat backup baru...")
    success, message = await tul.backup_system()
    if success:
        print(f"✅ Backup: {message}")
    else:
        print(f"❌ Backup gagal: {message}")
        
    print("\n✅ Maintenance selesai")
    input("Tekan Enter untuk kembali ke menu...")
    
async def rotate_vpn(tul):
    """Rotate VPN for an account"""
    print("\n" + "=" * 50)
    print("ROTATE VPN")
    print("=" * 50)
    
    phone = input("Nomor telepon (+62xxx): ")
    
    # Check if account exists
    if not tul.db.account_exists(phone):
        print(f"❌ Akun {phone} tidak ditemukan")
        input("Tekan Enter untuk kembali ke menu...")
        return
        
    print(f"Merotasi VPN untuk akun {phone}...")
    success = tul.vpn_manager.rotate_vpn(phone)
    
    if success:
        print(f"✅ VPN berhasil dirotasi untuk {phone}")
    else:
        print(f"❌ Gagal merotasi VPN untuk {phone}")
        
    input("Tekan Enter untuk kembali ke menu...")
    
async def run_cli(tul):
    """Run the interactive CLI"""
    while True:
        choice = await display_menu()
        
        if choice == '0':
            print("Keluar dari program...")
            break
        elif choice == '1':
            await add_account(tul)
        elif choice == '2':
            await add_multiple_accounts(tul)
        elif choice == '3':
            await check_account(tul)
        elif choice == '4':
            await check_all_accounts(tul)
        elif choice == '5':
            await list_accounts(tul)
        elif choice == '6':
            await delete_account(tul)
        elif choice == '7':
            await backup_system(tul)
        elif choice == '8':
            await maintenance(tul)
        elif choice == '9':
            await rotate_vpn(tul)
        else:
            print("Pilihan tidak valid!")
            input("Tekan Enter untuk mencoba lagi...")
