import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Explicitly load .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    PROPAGATE_EXCEPTIONS = True
    RESTX_MASK_SWAGGER = False
    RESTX_MASK_HEADER = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    CHAT_ID = os.environ.get('CHAT_ID')
