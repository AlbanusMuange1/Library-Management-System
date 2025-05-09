#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Book
from app.schemas.book import BookSchema
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required


books_bp = Blueprint('books', __name__)
book_schema = BookSchema()
books_schema = BookSchema(many=True)

@books_bp.route('/', methods=['GET'])
@jwt_required()
def get_books():
    try:
        query = Book.query
        title = request.args.get('title')
        author = request.args.get('author')
        category = request.args.get('category')

        if title:
            query = query.filter(Book.title.ilike(f'%{title}%'))

        if author:
                query = query.filter(Book.ilike(f'%{author}%'))

        if category:
             query = query.filter(Book.category.ilike(f'%{category}%'))

        books = query.all()
        return jsonify(books_schema.dump(books)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

@books_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
@role_required('admin', 'librarian')
def add_book():
     try:
          data = request.get_json()
          errors = book_schema.validate(data)
          if errors:
               return jsonify(errors), 400
          book = Book(
               title=data['title'],
               author=data['author'],
               category=data['category'],
               total_copies=data['total_copies'],
               available_copies=data['total_copies']
          )
          db.session.add(book)
          db.session.commit()
          return jsonify(book_schema.dump(book)), 201
     except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500
     

@books_bp.route('/<int:book_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'librarian')
def update_book(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        data = request.get_json()
        errors = book_schema.validate(data, partial=True)
        if errors:
             return jsonify(errors), 400
        
        book.title = data.get('title', book.title)
        book.author = data.get('author', book.author)
        book.category = data.get('category', book.category)
        book.total_copies = data.get( 'total_copies', book.total_copies)

        new_total = data.get('total_copies')
        if new_total is not None and new_total >= (book.total_copies - book.available_copies):
             diff = new_total - book.total_copies
             book.available_copies += diff if diff > 0 else 0

        db.session.commit()
        return jsonify(book_schema.dump(book)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500


@books_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_book(book_id):
     try:
        book = Book.query.get_or_404(book_id)
        db.session.delete(book)
        db.session.commit()
        return jsonify({'msg': 'Book deleted successfully'}), 200
     except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

@books_bp.route('/search', methods=['GET'])
def search_books():
    try:
          title = request.args.get('title', '').strip().lower()
          author = request.args.get('author', '').strip().lower()
          category = request.args.get('category', '').strip().lower()

          query = Book.query
          if title:
               query = query.filter(Book.title.ilike(f'%{title}%'))
          if author:
               query = query.filter(Book.author.ilike(f"%{author}%"))
          if category:
               query = query.filter(Book.category.ilike(f"%{category}%"))
          
          books = query.all()
          if not books:
               return jsonify({'msg': 'No books found'}), 404
          
          return jsonify({
            'books': [
                {'id': book.id, 'title': book.title, 'author': book.author, 
                 'category': book.category, 'available_copies': book.available_copies}
                for book in books
                    ]
               }), 200
    except Exception as e:
         return jsonify({'msg': 'An error occurred', 'error': str(e)})




                