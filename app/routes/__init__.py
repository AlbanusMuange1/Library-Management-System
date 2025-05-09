#!/usr/bin/env python3
from .auth import auth_bp
from .books import books_bp
from .members import members_bp
from .borrow import borrow_bp
from .debt import debt_bp
from .export import export_bp
from .mpesa import mpesa_bp

def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(books_bp, url_prefix='/api/books')
    app.register_blueprint(members_bp, url_prefix='/api/members')
    app.register_blueprint(borrow_bp, url_prefix='/api/borrow')
    app.register_blueprint(debt_bp, url_prefix='/api/debts')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(mpesa_bp, url_prefix='/api/mpesa')
    return app
