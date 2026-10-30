# Flask POS System

A comprehensive, desktop-ready Point of Sale (POS) and inventory management web application built with Python, Flask, SQLite, and AdminLTE.

---

## 🌟 Key Features

- **Interactive POS Screen**: Fast product search, responsive cart, quantity adjustments, tax & discount calculation, and multi-payment checkout.
- **Inventory & Store Management**: Complete management of Shops, Categories, Products, and Payment Methods.
- **Analytics & Reports**:
  - Daily & monthly sales reports with PDF invoice downloads.
  - Comprehensive income & profit margin reports with Excel (`.xlsx`) export.
- **Role-Based Authentication**: Secure session-based authentication with `admin` and `student` roles.
- **Automated Database Backups to Telegram**:
  - Safely snapshots the live SQLite database without locking conflicts using SQLite's online backup API.
  - Sends the backup file directly to a Telegram chat using bot credentials from `.env`.
  - Available via web UI, Flask CLI, or standalone Python script.
- **Standalone Windows Executable (`.exe`)**:
  - Compiles into a single portable `.exe` using PyInstaller.
  - Automatically keeps `app.db`, `.env`, and `uploads/` in the **exact same directory as the `.exe`**.
  - Powered by Waitress WSGI server with automatic browser launching on startup.

---

## 📋 Default Credentials

When first run without an existing database, the system automatically initializes all tables and creates a default administrator account:

- **Username:** `admin`
- **Password:** `admin`

---

## 🚀 Quick Start (Development)

### 1. Clone & Set Up Virtual Environment

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Configure Environment Variables

Copy the example `.env` file:

```powershell
cp .env.example .env
```

Edit `.env` to configure your settings and Telegram credentials:

```env
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=sqlite:///app.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Telegram Backup Credentials
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_telegram_chat_id_here
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Database Setup

```powershell
# Apply migrations
flask --app app db upgrade

# (Optional) Seed mockup catalog data
flask --app app seed-db
```

### 5. Run the Application

```powershell
# Development mode with auto-reload:
flask --app app run

# Or run with the production desktop server (Waitress):
python app.py
```

Open your browser at **`http://127.0.0.1:5000`**.

---

## 📦 Database Backup to Telegram

You can back up the database and send the file to Telegram through any of the following methods:

### Method 1: Web Dashboard (Admin)
1. Log in to the dashboard as an `admin`.
2. In the left sidebar under **SYSTEM & TOOLS**, click **Backup to Telegram**.
3. Confirm the prompt to immediately dispatch the backup.

### Method 2: Flask CLI Command
```powershell
flask --app app backup-db
```

### Method 3: Standalone Python Script
```powershell
# Send standard .db snapshot
python backup.py

# Send compressed .zip archive
python backup.py --compress
```

---

## 🛠️ Building the Windows Executable (`.exe`)

You can compile the entire project into a single, portable Windows desktop executable with any of these commands:

### Option 1: Flask CLI (Recommended)
```powershell
flask build-exe
```

### Option 2: Windows Batch File (Command Prompt or Double-Click)
```cmd
build.bat
```

### Option 3: PowerShell Script
```powershell
.\build.ps1
```

### Option 4: Direct PyInstaller
```powershell
pyinstaller --noconfirm flask_pos.spec
```

The compiled binary will be placed at:
```
dist/flask_pos.exe
```

---

## 📂 Portable Executable Layout

When deploying `dist/flask_pos.exe` to another computer, all persistent files remain alongside the `.exe`:

```text
MyPOS/
├── flask_pos.exe       # Standalone executable
├── app.db              # SQLite database (auto-created in same folder)
├── .env                # (Optional) Bot token & custom configuration
├── uploads/            # (Auto-created) Product & shop logos
└── backups/            # (Auto-created) Local database backups
```

---

## 📁 Project Structure

```text
flask_pos/
├── app.py                      # Application factory, routes, and server entrypoint
├── backup.py                   # Telegram database backup module & CLI
├── build.bat                   # 1-click Windows build script
├── build.ps1                   # PowerShell build script
├── config.py                   # Configuration & runtime path resolution
├── extensions.py               # SQLAlchemy, LoginManager, Limiter extensions
├── flask_pos.spec              # PyInstaller build specification
├── models.py                   # Database models (User, Shop, Product, Sale, etc.)
├── seed.py                     # Initial seed data script
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration
├── blueprints/
│   └── dashboard/              # Web dashboard & POS interface routes
├── templates/
│   └── admin/                  # AdminLTE Jinja2 templates (POS, reports, CRUD)
├── static/                     # CSS, JavaScript, and image assets
└── dist/
    └── flask_pos.exe           # Compiled desktop executable
```

---

## 📄 License

This project is open-source and available under the MIT License.
