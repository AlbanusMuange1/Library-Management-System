#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User
from app.schemas.user import UserSchema
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required

members_bp = Blueprint('members', __name__)
user_schema = UserSchema()
users_schema = UserSchema(many=True)


@members_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin', 'librarian')
def get_members():
    try:
        members = User.query.filter(User.role != 'admin').all()
        return jsonify(users_schema.dump(members)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@members_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@role_required('admin', 'librarian')
def get_member(user_id):
    try:
        member = User.query.get_or_404(user_id)
        if member.role == 'admin':
            return jsonify({'msg': 'Admins cannot be accessed via this endpoint'}), 403

        return jsonify(user_schema.dump(member)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@members_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_member(user_id):
    try:
        member = User.query.get_or_404(user_id)

        if member.role == 'admin':
            return jsonify({'msg': 'Admins cannot be modified here'}), 403

        data = request.get_json()
        errors = user_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        member.name = data.get('name', member.name)
        member.email = data.get('email', member.email)
        member.role = data.get('role', member.role)

        db.session.commit()
        return jsonify(user_schema.dump(member)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@members_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_member(user_id):
    try:
        member = User.query.get_or_404(user_id)

        if member.role == 'admin':
            return jsonify({'msg': 'Admins cannot be deleted'}), 403

        db.session.delete(member)
        db.session.commit()
        return jsonify({'msg': 'Member deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
