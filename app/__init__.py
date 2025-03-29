#!/usr/bin/env python3
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, bcrypt, ma, mail
from .routes import register_routes
from flask_mail import Mail


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    ma.init_app(app)
    mail.init_app(app)


    register_routes(app)
    return app