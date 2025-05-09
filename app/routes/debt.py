#!/usr/bin/env python3
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import Debt
from sqlalchemy.orm import joinedload

debt_bp = Blueprint('debt', __name__)
@debt_bp.route('/my-fines', methods=['GET'])
@jwt_required()
def get_user_fines():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        role = claims.get('role')

        debts = []
        total_fines = 0

        if role in ['admin', 'librarian']:
            debts = Debt.query.options(
                joinedload(Debt.user), joinedload(Debt.book)
            ).order_by(Debt.created_at.desc()).all()

        elif role == 'member':
            debts = Debt.query.options(joinedload(Debt.book)).filter_by(user_id=user_id).order_by(Debt.created_at.desc()).all()

        else:
            return jsonify({'error': 'Unauthorized access'}), 403

        debt_list = []

        for debt in debts:
            book = debt.book
            user = debt.user

            debt_data = {
                "book_title": book.title if book else "Unknown",
                "days_overdue": debt.days_overdue,
                "fine_amount": debt.fine_amount,
                "paid": debt.paid,
                "created_at": debt.created_at.strftime("%Y-%m-%d") if debt.created_at else None,
            }

            if role == 'member':
                if not debt.paid:
                    total_fines += debt.fine_amount

            if role in ['admin', 'librarian'] and user:
                debt_data["user"] = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                }

            debt_list.append(debt_data)

        response = {
            "debts": debt_list
        }

        if role == 'member':
            response["total_fines"] = total_fines
        else:
            response["total_debts"] = len(debt_list)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'msg': f"Error fetching fines: {str(e)}"}), 500
