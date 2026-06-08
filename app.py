import os
from flask import Flask
from blueprints.api import api_bp
from blueprints.dashboard import dashboard_bp
from extensions import db, migrate, login_manager, jwt
from config import Config
from flask_dotenv import DotEnv
import models  # import models to register with SQL Alchemy

app = Flask(__name__)
app.config.from_object(Config)

# Load environment variables
env = DotEnv(app)
env.eval({'SQLALCHEMY_TRACK_MODIFICATIONS': bool})

# Resolve relative sqlite database URI to absolute path
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
if db_uri and db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:////'):
    db_file = db_uri[10:]
    basedir = os.path.abspath(os.path.dirname(__file__))
    if not os.path.isabs(db_file):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, db_file)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
jwt.init_app(app)
login_manager.login_view = 'dashboard.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# Auto-seed a default user
with app.app_context():
    try:
        if models.User.query.first() is None:
            admin = models.User(username='admin', status='approve', type='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Auto-seeded default admin user (admin / admin)")
    except Exception as e:
        print(f"Error seeding database: {e}")

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/')

# Register custom CLI commands
@app.cli.command("seed-db")
def seed_db_command():
    """Seeds the database with initial mockup data."""
    from seed import seed_data
    seed_data()

if __name__ == "__main__":
    app.run(debug=True)
