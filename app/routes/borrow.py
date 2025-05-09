#!/usr/bin/env python3
import time
import pytz
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, mail
from app.models import Book, Borrow, Debt
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.utils.decorators import role_required
from datetime import datetime, timedelta
from flask_mail import Message
from threading import Thread

borrow_bp = Blueprint('borrow', __name__)

BORROW_DAYS_LIMIT = -14
FINE_PER_DAY = 20  
kenya_tz = pytz.timezone("Africa/Nairobi")

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {str(e)}")

def send_borrow_email(user_email, book_title, due_date):
    app = current_app._get_current_object()
    msg = Message('Book Borrowed Successfully', recipients=[user_email])
    msg.body = f"""
    Hello,

    You have successfully borrowed the book **"{book_title}"**.

    The book is due on **"{due_date}"** Return in time to avoid fine.

    Happy Reading

    Kenya Library Management System
    """
    Thread(target=send_async_email, args=(app, msg)).start()

def delayed_email_send(app, msg, delay):
    time.sleep(delay) 
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send reminder email: {str(e)}")

    
def schedule_reminder_email(user_email, book_title, due_date):
    """Schedule an email reminder 2 days before the due date."""
    reminder_date = due_date - timedelta(days=2)

    if datetime.utcnow() > reminder_date:
        return  # Don't send if past reminder date

    app = current_app._get_current_object()  # Get Flask app context

    msg = Message("⏳ Book Return Reminder!",
                  recipients=[user_email])
    msg.body = f"""
    Hello,

    This is a reminder that your borrowed book **"{book_title}"** is due on **{due_date.strftime('%Y-%m-%d')}**.
    Please return it on time to avoid late fees.

    Thank you!

    Library Management System
    """

    delay_seconds = (reminder_date - datetime.utcnow()).total_seconds()
    Thread(target=delayed_email_send, args=(app, msg, delay_seconds)).start()


@borrow_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@role_required('member', 'admin', 'librarian')
def borrow_book():
    try:
        data = request.get_json()
        # print("Received data:", data)

        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid request format'}), 400

        book_id = data.get('book_id')
        # print("Extracted Book ID:", book_id)

        if not book_id:
            return jsonify({'msg': 'Book ID is required'}), 400

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'msg': 'Book not found'}), 404

        if book.available_copies < 1:
            return jsonify({'msg': 'Book is currently unavailable'}), 400

        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get("role")
        user_email = claims.get("email")

        # print(f"Decoded JWT Identity: {user_id}")
        # print(f"Decoded JWT Role: {user_role}")
        # print(f"Decoded JWT Email: {user_email}")

        if role == "member":
            unpaid_debt = Debt.query.filter_by(user_id=user_id, paid=False).first()
            if unpaid_debt:
                return jsonify({
                    'msg': 'You have an unpaid debt. Please settle it before borrowing more books.',
                }), 403

        existing_borrow = Borrow.query.filter_by(user_id=user_id, book_id=book_id, returned=False).first()
        if existing_borrow:
            return jsonify({'msg': 'You already borrowed this book and have not returned it'}), 400

        borrow_date = datetime.now(kenya_tz).replace(microsecond=0)
        due_date = borrow_date + timedelta(days=BORROW_DAYS_LIMIT)

        new_borrow = Borrow(
            user_id=user_id,
            book_id=book_id,
            borrow_date=borrow_date,
            due_date=due_date,
            returned=False
        )

        book.available_copies -= 1
        db.session.add(new_borrow)
        db.session.commit()

        send_borrow_email(user_email, book.title, due_date)

        schedule_reminder_email(user_email, book.title, due_date)

        return jsonify({
            'msg': f'Book "{book.title}" borrowed successfully!',
            'due_date': due_date.strftime('%Y-%m-%d')
        }), 201
    except Exception as e:
        return jsonify({'msg': str(e)}), 500


@borrow_bp.route('/return/<int:book_id>', methods=['PUT'])
@jwt_required()
@role_required('member', 'librarian')
def return_book(book_id):
    try:
        user_id = get_jwt_identity()
        # print(f"User ID: {user_id}, Book ID: {book_id}")

        borrow_record = Borrow.query.filter_by(
            user_id=user_id, book_id=book_id, returned=False
        ).first()
        
        # print(f"Borrow Record Found: {borrow_record}")

        if not borrow_record:
            return jsonify({'msg': 'Book already returned or Book never borrowed'}), 400

        book = Book.query.get(book_id)
        if not book:
            return jsonify({'msg': 'Book not found'}), 404

        return_date = datetime.utcnow()
        overdue_days = max((return_date - borrow_record.due_date).days, 0)
        fine_amount = overdue_days * FINE_PER_DAY

        borrow_record.return_date = return_date
        borrow_record.fine = fine_amount
        borrow_record.returned = True
        book.available_copies += 1

        if overdue_days > 0:
            debt = Debt(
                user_id=user_id,
                book_id=book_id,
                days_overdue=overdue_days,
                fine_amount=fine_amount,
                paid=False
            )
            db.session.add(debt)

        db.session.commit()

        return jsonify({
            'msg': f'Book \"{book.title}\" returned successfully!',
            'fine': fine_amount if fine_amount > 0 else 0,
            'overdue_days': overdue_days
        }), 200
    except Exception as e:
        return jsonify({'msg': str(e)}), 500


@borrow_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin', 'librarian')
def list_borrowed_books():
    try:
        borrowed_books = Borrow.query.filter_by(returned=False).all()
        if not borrowed_books:
            return jsonify({'msg': 'No books are currently borrowed'}), 200

        borrowed_list = [{
            'borrow_id': b.id,
            'user_id': b.user_id,
            'book_id': b.book_id,
            'borrow_date': b.borrow_date.strftime('%Y-%m-%d'),
            'due_date': b.due_date.strftime('%Y-%m-%d'),
            'returned': b.returned
        } for b in borrowed_books]

        return jsonify(borrowed_list), 200
    except Exception as e:
        return jsonify({'msg': str(e)}), 500
