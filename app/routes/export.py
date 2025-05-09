#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.exports.exporter import export_to_csv, export_to_excel
from app.models import Book, User, Borrow, Debt
from sqlalchemy.exc import SQLAlchemyError
import logging

export_bp = Blueprint("export", __name__)

logger = logging.getLogger(__name__)

def is_admin_or_librarian():
    role = get_jwt().get('role')
    return role in ["admin", "librarian"]

def handle_export(data, columns, format, filename):
    if not data:
        return jsonify({'msg': 'No record found to export'}), 404
    if format == 'excel':
        return export_to_excel(data, columns, filename)
    elif format == 'csv':
        return export_to_csv(data, columns, filename)
    else:
        return jsonify({'msg': 'Invalid format'}), 400
    

@export_bp.route('/books/<string:format>', methods=['GET'])
@jwt_required()
def export_books(format):
    if not is_admin_or_librarian():
        return jsonify({'msg': 'Access denied'}), 403
    try:
        books = Book.query.all()
        data = [[b.id, b.title, b.author, b.category, b.total_copies, b.available_copies] for b in books]
        columns = ['ID', 'Title', 'Author', 'Category', 'Total Copies', 'Available Copies']
        return handle_export(data, columns, format, 'books.xlsx')
    
    except SQLAlchemyError as e:
        logger.exception('Error exporting books')
        return jsonify({'msg': 'Failed to export books', 'error': str(e)}), 500
    
@export_bp.route('/members/<string:format>', methods=['GET'])
@jwt_required()
def export_members(format):
    if not is_admin_or_librarian():
        return jsonify({'msg': 'Access denied'}), 403
    try:
        users = User.query.all()
        data = [[u.id, u.name, u.email, u.role] for u in users]
        columns = ['ID', 'Name', 'Email', 'Role']
        return handle_export(data, columns, format, 'members.xlsx')
    
    except SQLAlchemyError as e:
        logger.exception('Error exporting members')
        return jsonify({'msg': 'Failed to export members', 'error': str(e)}), 500
    
@export_bp.route('/borrows/<string:format>', methods=['GET'])
@jwt_required()
def export_borrows(format):
    if not is_admin_or_librarian():
        return jsonify({'msg': 'Access denied'}), 403
    try:
        borrows = Borrow.query.all()
        data = [[b.id, b.user.name if b.user else 'Unknown', b.book.title if b.book else 'Unknown', b.borrow_date.strftime('%Y-%m-%d'), b.due_date.strftime('%Y-%m-%d'), b.returned] for b in borrows]
        columns = ['ID', 'User', 'Book', 'Borrow Date', 'Due Date', 'Returned']
        return handle_export(data, columns, format, 'borrows.xlsx')
    except SQLAlchemyError as e:
        logger.exception('Error exporting borrows')
        return jsonify({'msg': 'Failed to export borrows', 'error': str(e)}), 500

@export_bp.route('/fines/<string:format>', methods=['GET'])
@jwt_required()
def export_fines(format):
    if not is_admin_or_librarian():
        return jsonify({'msg': 'Access denied'}), 403
    try:
        debts = Debt.query.all()
        data = [[d.id, d.user.name if d.user else 'Unknown', d.user.email if d.user else 'Unknown', d.book.title if d.book else 'Unknown', d.days_overdue, d.fine_amount, "Yes" if d.paid else "No"] for d in debts]
        columns = ['ID', 'User', 'Email', 'Book', 'Days Overdue', 'Fine', 'Paid']
        return handle_export(data, columns, format, 'fines.xlsx')
    except SQLAlchemyError as e:
        logger.exception('Error exporting fines')
        return jsonify({'msg': 'Failed to export fines', 'error': str(e)}), 500