# Telethon Unlimited Login

Sistem manajemen multiple akun Telegram menggunakan Telethon

## Instalasi

```bash
# Clone repository
git clone https://github.com/username/telethon-unlimited-login.git
cd telethon-unlimited-login

# Install dependencies
pip install -r requirements.txt
```

## Konfigurasi

Edit file `config.json` dan sesuaikan dengan kebutuhan:

```json
{
    "api_id": 12345,
    "api_hash": "0123456789abcdef0123456789abcdef",
    "2fa_password": "Dgvt61zwe@",
    "admin_notification_id": null,
    "default_vpn": "cloudflare"
}
```

## Penggunaan

### Command Line

```bash
# Menjalankan CLI Interaktif
python main.py --cli

# Tambah akun baru
python main.py --add +628123456789

# Cek akun
python main.py --check +628123456789

# Cek semua akun
python main.py --check-all

# Tampilkan daftar akun
python main.py --list

# Hapus akun
python main.py --delete +628123456789

# Backup sistem
python main.py --backup
```

## Struktur Folder

- `accounts/accounts.db` - Database info akun
- `sessions/*.session` - File session per akun
- `logs/` - Log aktivitas & error
- `backup/` - Auto-backup DB & session

## Fitur

### Fitur Inti
- Validasi Format Nomor HP (+62)
- Login & Simpan Akun ke SQLite
- Session Disimpan ke Folder
- Gunakan 2FA default otomatis jika diminta (Dgvt61zwe@)
- Auto-Deteksi Session Mati / Expired / Banned
- Update Status Akun di DB (active, banned, 2fa_error, dll)
- Auto-Cek Session Valid Saat Startup
- Struktur Folder Otomatis Dibuat jika belum ada

### Tool CLI
- Tambah Akun via CLI (satu per satu / batch)
- Lihat Semua Akun Aktif
- Uji Koneksi Akun (ping session)
- Hapus Akun / Session dari DB + File

### Fitur Tambahan
- VPN Per Akun (disimpan di DB) default CF 1.1.1.1
- Penanda "used" / "idle" Akun di DB
- Notifikasi ke Telegram ADMIN_ID (gagal / berhasil login)

### Keamanan & Stabilitas
- Kunci API_ID/API_HASH di config file
- Session Recovery Tool (ganti nama, relogin jika error)

### Pemeliharaan Otomatis
- Log Gagal Login ke logs/failed.txt
- Log Aktivitas Login per Akun
- Auto-Backup DB & Session Berkala
- Periksa Session File Saat Load (jika hilang/rusak)
- Dynamic Module Loading

## Ruang Pengembangan Jangka Panjang

### Struktur dan Manajemen Akun
- **Dashboard UI WEB**

### Modularitas & Otomasi
- **Plugin System (bot, autoresponder, broadcast, dll per akun)**
- **Scheduler atau Cron di setiap akun (jadwal aktif / post / follow up)**
- **Auto-Rotate Akun (misal 10 akun ganti setiap 10 menit)**
- **Scheduler for Automated Tasks**
- **Automated Message Management**

### Integrasi Gaya & Interaksi
- **Sistem Gaya Chat (formal, santai, boomer, bocil, dll)**
- **Wordlist / Kamus Gaya Per Akun**
- **Integrasi ke AI Chat API (OpenAI, Gemini, dll)**

### Jaringan & Identitas
- **Per-Akun Proxy Management**
- **Per-Akun Device Spoofing (misal set Android/iPhone)**
- **Simulasi Aktivitas Manual (baca, ketik, ngetap profil, dll)**

### Monitoring & Logging
- **Live Log (via web atau file)**
- **Activity Tracker per akun (statistik basic)**
- **Auto-recovery jika crash atau banned**
