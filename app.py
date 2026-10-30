import os
import sys
from flask import Flask, send_from_directory
from blueprints.dashboard import dashboard_bp
from extensions import db, migrate, login_manager, limiter
from config import Config
from flask_dotenv import DotEnv
import models  # import models to register with SQLAlchemy

# Runtime environment detection
if getattr(sys, 'frozen', False):
    basedir = os.path.dirname(sys.executable)
    bundle_dir = getattr(sys, '_MEIPASS', basedir)
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    bundle_dir = basedir

# Locate templates and static assets
template_dir = os.path.join(bundle_dir, 'templates')
static_dir = os.path.join(bundle_dir, 'static')

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)
app.config.from_object(Config)

# Set persistent external upload directory in the SAME directory as the .exe
uploads_dir = os.path.join(basedir, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)
app.config['UPLOAD_FOLDER'] = uploads_dir

# Serve uploaded media from external persistent uploads folder
@app.route('/uploads/<path:filename>')
@app.route('/static/uploads/<path:filename>')
def serve_uploaded_media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Load environment variables if .env exists next to the .exe
env_file = os.path.join(basedir, '.env')
if os.path.exists(env_file):
    env = DotEnv(app)
    env.eval({'SQLALCHEMY_TRACK_MODIFICATIONS': bool})

# Ensure SQLite database URI points to the directory of the .exe
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
if db_uri and db_uri.startswith('sqlite:///'):
    db_file = db_uri[10:]
    # If not absolute (e.g. app.db)
    if not os.path.isabs(db_file) and not (len(db_file) > 1 and db_file[1] == ':'):
        resolved_db_path = os.path.join(basedir, db_file).replace('\\', '/')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{resolved_db_path}'

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
limiter.init_app(app)
login_manager.login_view = 'dashboard.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# Ensure database tables exist and auto-seed default admin user
with app.app_context():
    try:
        db.create_all()
        if models.User.query.first() is None:
            admin = models.User(username='admin', status='approve', type='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Auto-seeded default admin user (admin / admin)")
    except Exception as e:
        print(f"Error seeding database: {e}")

# Register blueprints
app.register_blueprint(dashboard_bp, url_prefix='/')

# Register custom CLI commands
@app.cli.command("seed-db")
def seed_db_command():
    """Seeds the database with initial mockup data."""
    from seed import seed_data
    seed_data()

@app.cli.command("backup-db")
def backup_db_command():
    """Backs up the SQLite database and sends the file to Telegram."""
    from backup import send_db_backup_to_telegram
    success, message = send_db_backup_to_telegram()
    if success:
        print(f"[SUCCESS] {message}")
    else:
        print(f"[ERROR] {message}")

@app.cli.command("build-exe")
def build_exe_command():
    """Builds the standalone .exe file using PyInstaller."""
    import subprocess
    print("=" * 60)
    print("  Building Windows executable using PyInstaller...")
    print("=" * 60)
    spec_path = os.path.join(basedir, "flask_pos.spec")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", spec_path]
    result = subprocess.run(cmd, cwd=basedir)
    if result.returncode == 0:
        dist_exe = os.path.join(basedir, "dist", "flask_pos.exe")
        print("=" * 60)
        print(f"  [SUCCESS] Executable built successfully!")
        print(f"  Output: {dist_exe}")
        print("=" * 60)
    else:
        print(f"  [ERROR] PyInstaller exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

def run_application():
    import webbrowser
    import threading

    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    local_url = f"http://127.0.0.1:{port}"

    print("=" * 60)
    print(f"  Flask POS Desktop Server")
    print(f"  Access URL: {local_url}")
    print(f"  Database:   {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print("=" * 60)

    # Launch browser automatically
    threading.Timer(1.5, lambda: webbrowser.open(local_url)).start()

    try:
        from waitress import serve
        print(f"  Production WSGI Server (Waitress) active on port {port}")
        serve(app, host=host, port=port)
    except ImportError:
        app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    run_application()
