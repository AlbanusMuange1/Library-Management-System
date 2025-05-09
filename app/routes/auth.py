#!/usr/bin/env python3
import re
import html
import random
import time
from datetime import timedelta
from flask import Blueprint, request, jsonify
from app.extensions import db, mail
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message


EMAIL_REGEX = r'^[a-zA-Z0-9_.+]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
NAME_REGEX = r'^[a-zA-Z0-9-_ ]+$'
PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"


auth_bp =Blueprint('auth', __name__)

VERIFICATION_CODES = {}

EXPIRATION_TIME = 36000

def generate_verification_code(email):
    code = random.randint(100000, 999999)
    VERIFICATION_CODES[email] = {
        'code': code,
        'timestamp': time.time()
    }
    return code

def is_code_valid(email, code):
    if email not in VERIFICATION_CODES:
        return False
    stored_data = VERIFICATION_CODES[email]

    if stored_data['code'] != int(code):
        return False
    if time.time() - stored_data['timestamp'] > EXPIRATION_TIME:
        del VERIFICATION_CODES[email]
        return False
    
    return True

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        # print(f"Received registration data: {data}")

        if not isinstance(data, dict):
            return jsonify({'msg': 'Invalid request format'}), 400
        
        name = str(data.get('name', '')).strip()
        email = str(data.get('email', '')).strip()
        password = str(data.get('password', '')).strip()
        role = str(data.get('role', 'member')).strip()

        if not name or not email or not password:
            return jsonify({'msg': 'Please fill in all fields'}), 400
        
        if User.query.filter_by(name=name).first():
            return jsonify({'msg': 'Username already exists'}), 400
        
        if not re.match(NAME_REGEX, name):
            return jsonify({'msg': 'Invalid username format'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'msg': 'Email already registered'}), 409
        
        if not re.match(EMAIL_REGEX, email):
            return jsonify({'msg': 'Invalid email format'}), 400

        if not re.match(PASSWORD_REGEX, password):
            return jsonify({'msg': 'Password must be at least 8 characters long, include one letter, one number, and one special character (@$!%*?&)' }), 400

        email = html.escape(email)

        user = User(name=name, email=email, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({'msg': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # print(f"Received login data: {data}")

        if not isinstance(data, dict):
            return jsonify({'msg': 'Invalid request format'}), 400
        
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', '')).strip()
        # print("Received data", email, password)

        if not email or not password:
            return jsonify({'msg': 'Please fill in all fields'}), 400
        
        if not re.match(EMAIL_REGEX, email):
            return jsonify({'msg': 'Invalid email format'}), 400
        
        email = html.escape(email)

        user = User.query.filter_by(email=email).first()
        # print(f"Check password: {user.check_password(password)}")
        
        if not user or not user.check_password(password):
            return jsonify({'msg': 'Invalid email or password'}), 401
        
        verification_code = generate_verification_code(email)
        msg = Message('Kenya Library Verification Code', recipients=[email])
        msg.body = f"Your 2FA verification code is: {verification_code}\nThis code expires in 10 minutes."
        mail.send(msg)

        return jsonify({'msg': '2FA code sent to email', 'email': email}), 200
        # expires = timedelta(hours=9)

        # access_token = create_access_token(identity={"id": user.id, "role": user.role, "email": user.email}, expires_delta=expires)
        # access_token = create_access_token(identity=str(user.id), additional_claims={
        #     "role": user.role,
        #     "email": user.email
        # }, expires_delta=expires)

        # return jsonify({
        #     'access_token': access_token,
        #     'user': {'id': user.id, 'role': user.role, 'email': user.email}
        # }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500
    

@auth_bp.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    try:
        data = request.json
        email = data.get('email')
        verification_code = data.get('code')
        # print(email, verification_code)

        if not email or not verification_code:
            return jsonify({'msg': 'Please fill in all fields'}), 400
        if not is_code_valid(email, verification_code):
            return jsonify({'msg': 'Invalid verification code'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'msg': 'User not found'}), 404
        
        expires = timedelta(hours=1)
        access_token = create_access_token(identity=str(user.id), additional_claims={
            "role": user.role,
            "email": user.email
        }, expires_delta=expires)

        del VERIFICATION_CODES[email]

        return jsonify({
            'msg': 'Login successfully',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'role': user.role,
                'email': user.email
            }
        }), 200

    except Exception as e:
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500   


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'logged_in_as': current_user}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'msg': 'User not found'})
    
    verification_code = generate_verification_code(email)

    msg = Message('Password Reset Code', recipients=[email])
    msg.body = f"You password reset code is: {verification_code}\nThis code expires in 10 minutes."
    mail.send(msg)

    return jsonify({'msg': 'Verification code sent to email'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    verification_code = data.get('code')
    new_password = data.get('new_password')

    if not email or not verification_code or not new_password:
        return jsonify({'msg': 'Missing required fields'}), 400
    if not is_code_valid(email, verification_code):
        return jsonify({'msg': 'Invalid verification code'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    user.set_password(new_password)
    db.session.commit()

    del VERIFICATION_CODES[email]
    return jsonify({'msg': 'Password reset successfully'}), 200
