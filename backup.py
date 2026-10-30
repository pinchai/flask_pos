import os
import sys
import sqlite3
import zipfile
import argparse
from datetime import datetime
import requests
from dotenv import load_dotenv

# Base directory for the Flask project or PyInstaller executable
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure environment variables are loaded from .env
load_dotenv(os.path.join(BASE_DIR, '.env'))


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_database_path() -> str:
    """
    Resolve the SQLite database file path from environment variables
    or default locations in the same directory as the executable.
    """
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    if db_uri and db_uri.startswith('sqlite:///'):
        db_file = db_uri.replace('sqlite:///', '', 1)
        if not os.path.isabs(db_file) and not (len(db_file) > 1 and db_file[1] == ':'):
            candidate = os.path.join(BASE_DIR, db_file)
        else:
            candidate = db_file
        if os.path.exists(candidate):
            return candidate

    # Check common fallback locations in the executable's directory
    candidates = [
        os.path.join(BASE_DIR, 'app.db'),
        os.path.join(BASE_DIR, 'instance', 'app.db')
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            return candidate

    # If file exists even with size 0, return first existing candidate
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(f"Database file could not be found. Checked URI: '{db_uri}' and paths: {candidates}")


def create_sqlite_snapshot(source_db_path: str, target_snapshot_path: str) -> None:
    """
    Safely create an online point-in-time snapshot of the SQLite database
    using SQLite's online backup API.
    """
    src_conn = sqlite3.connect(source_db_path)
    dest_conn = sqlite3.connect(target_snapshot_path)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()


def create_backup_file(output_dir: str = "backups", compress: bool = False) -> str:
    """
    Creates a database backup file in output_dir.
    If compress=True, returns the path to a .zip archive.
    Otherwise, returns the path to a .db snapshot.
    """
    db_path = get_database_path()
    abs_output_dir = os.path.join(BASE_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
    os.makedirs(abs_output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(os.path.basename(db_path))[0]
    
    snapshot_filename = f"{base_name}_backup_{timestamp}.db"
    snapshot_path = os.path.join(abs_output_dir, snapshot_filename)

    # 1. Create a safe SQLite snapshot
    create_sqlite_snapshot(db_path, snapshot_path)

    # 2. Optionally compress into a ZIP file
    if compress:
        zip_filename = f"{base_name}_backup_{timestamp}.zip"
        zip_path = os.path.join(abs_output_dir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(snapshot_path, arcname=snapshot_filename)
        
        # Remove uncompressed snapshot to save space
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
        return zip_path

    return snapshot_path


def send_file_to_telegram(
    file_path: str,
    bot_token: str = None,
    chat_id: str = None,
    caption: str = None,
    timeout: int = 60
) -> tuple[bool, str]:
    """
    Uploads a file to Telegram using the sendDocument Bot API method.
    """
    token = bot_token or os.environ.get('BOT_TOKEN')
    target_chat_id = chat_id or os.environ.get('CHAT_ID')

    if not token or not target_chat_id:
        return False, "Telegram credentials missing: BOT_TOKEN and CHAT_ID must be set in .env."

    if not os.path.exists(file_path):
        return False, f"Backup file does not exist: {file_path}"

    filename = os.path.basename(file_path)
    file_size_bytes = os.path.getsize(file_path)
    file_size_formatted = format_file_size(file_size_bytes)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not caption:
        caption = (
            f"📦 <b>Flask POS Database Backup</b>\n\n"
            f"📁 <b>File:</b> <code>{filename}</code>\n"
            f"💾 <b>Size:</b> <code>{file_size_formatted}</code>\n"
            f"📅 <b>Date:</b> <code>{now_str}</code>\n"
            f"✅ <b>Status:</b> Completed successfully"
        )

    api_url = f"https://api.telegram.org/bot{token}/sendDocument"

    try:
        with open(file_path, 'rb') as doc_file:
            data = {
                'chat_id': target_chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            files = {
                'document': (filename, doc_file, 'application/octet-stream')
            }
            response = requests.post(api_url, data=data, files=files, timeout=timeout)

        result = response.json()
        if response.status_code == 200 and result.get('ok'):
            return True, f"Backup file '{filename}' ({file_size_formatted}) sent successfully to Telegram."
        else:
            err_desc = result.get('description', response.text)
            return False, f"Telegram API error (code {response.status_code}): {err_desc}"

    except requests.exceptions.RequestException as e:
        return False, f"Network error sending backup to Telegram: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def send_db_backup_to_telegram(
    compress: bool = False,
    keep_local: bool = True,
    output_dir: str = "backups",
    bot_token: str = None,
    chat_id: str = None
) -> tuple[bool, str]:
    """
    High-level function:
    1. Creates consistent point-in-time database snapshot (or zip archive)
    2. Sends the file to Telegram using credentials from .env
    3. Retains or removes local copy based on keep_local
    """
    try:
        backup_file = create_backup_file(output_dir=output_dir, compress=compress)
    except Exception as e:
        return False, f"Database backup creation failed: {str(e)}"

    success, msg = send_file_to_telegram(
        file_path=backup_file,
        bot_token=bot_token,
        chat_id=chat_id
    )

    if not keep_local and os.path.exists(backup_file):
        try:
            os.remove(backup_file)
        except OSError:
            pass

    return success, msg


def main():
    parser = argparse.ArgumentParser(description="Backup SQLite database and send it to Telegram.")
    parser.add_argument(
        "--compress", "-c",
        action="store_true",
        help="Compress database backup into a .zip file before sending."
    )
    parser.add_argument(
        "--no-keep-local",
        action="store_true",
        help="Do not keep the local backup file in the backups folder after sending."
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="backups",
        help="Directory to store local backup files (default: 'backups')."
    )

    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting database backup...")
    success, message = send_db_backup_to_telegram(
        compress=args.compress,
        keep_local=not args.no_keep_local,
        output_dir=args.output_dir
    )

    if success:
        print(f"[SUCCESS] {message}")
        sys.exit(0)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
