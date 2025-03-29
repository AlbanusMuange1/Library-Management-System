#!/usr/bin/env python3
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
        # SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
        SECRET_KEY = os.getenv('SECRET_KEY')
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
        # JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
        JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=9)
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        if not SECRET_KEY or not SQLALCHEMY_DATABASE_URI:
            raise ValueError('Missing environment variables: Ensure SECRET_KEY and DATABASE_URI')
        MAIL_SERVER = os.getenv('MAIL_SERVER')
        MAIL_PORT = os.getenv('MAIL_PORT')
        MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
        MAIL_USERNAME = os.getenv('MAIL_USERNAME')
        MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
        MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')


if __name__ == "__main__":
    try:
        config = Config()
        print("Config loaded successfully")
    except ValueError as e:
        print(f"Config Error: {e}")