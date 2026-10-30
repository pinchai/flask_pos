import os
import sys
from dotenv import load_dotenv

# Detect runtime environment (PyInstaller frozen executable vs standard Python)
if getattr(sys, 'frozen', False):
    basedir = os.path.dirname(sys.executable)
    bundle_dir = getattr(sys, '_MEIPASS', basedir)
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    bundle_dir = basedir

# Priority 1: Load .env from directory containing the executable
env_file = os.path.join(basedir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Priority 2: Fallback to bundled or local root
    load_dotenv(os.path.join(bundle_dir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-12345'
    PROPAGATE_EXCEPTIONS = True
    
    # SQLite database defaults to app.db in the SAME directory as the .exe
    default_db_file = os.path.join(basedir, 'app.db').replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('SQLALCHEMY_DATABASE_URI') or
        os.environ.get('DATABASE_URL') or
        f'sqlite:///{default_db_file}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    CHAT_ID = os.environ.get('CHAT_ID')
