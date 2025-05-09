#!/usr/bin/env python3
from .extensions import db, bcrypt
from datetime import datetime, timedelta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), default='member')


    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    total_copies = db.Column(db.Integer, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)


class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    due_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    fine = db.Column(db.Float, default=0.0)
    returned = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='borrows')
    book = db.relationship('Book', backref='borrows')

class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    days_overdue = db.Column(db.Integer, nullable=False)
    fine_amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=3))

    user = db.relationship('User', backref='debts')
    book = db.relationship('Book', backref='debts')