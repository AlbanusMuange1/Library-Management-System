#!/usr/bin/env python3
import os
import requests
import base64
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Debt, User
from app.extensions import db
from app.utils.pdf_generator import generate_receipt_pdf
from app.utils.emailer import send_email_with_attachment

mpesa_bp = Blueprint('mpesa', __name__)

def get_access_token():
    try:
        auth = (os.getenv('MPESA_CONSUMER_KEY'), os.getenv('MPESA_CONSUMER_SECRET'))
        headers = {"Content-Type": "application/json"}
        res = requests.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            auth=auth,
            headers=headers
        )
        res.raise_for_status()
        return res.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None
    
def build_stk_payload(phone, amount):
    shortcode = os.getenv("MPESA_SHORTCODE", "174379")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    passkey = os.getenv("MPESA_PASSKEY")
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()
    return {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": os.getenv("MPESA_CALLBACK_URL"),
        "AccountReference": "LibraryFine",
        "TransactionDesc": "Library Fine Payment"
    }

@mpesa_bp.route('/stk', methods=['POST'])
@jwt_required()
def initiate_stk_push():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not data.get('phone') or not data.get('amount'):
            return jsonify({"msg": "Phone number and amount is required"}), 400
        phone = data.get('phone')
        try:
            amount = float(data.get('amount'))
        except ValueError:
            return jsonify({"msg": "Amount must be number"}), 400
        print(f"Phone {phone}, Amount: {amount}")
        unpaid_debts = Debt.query.filter_by(user_id=user_id, paid=False).all()
        total_debt = sum(d.fine_amount for d in unpaid_debts)
        
        if amount < total_debt:
            return jsonify({'msg': f"Insufficient amount. Total fines: {total_debt}"})
        
        # timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # password = base64.b64encode((os.getenv("MPESA_SHORTCODE") + os.getenv("MPESA_PASSKEY") + timestamp).encode()
        # ).decode()
        
        # payload = {
        #     "BusinessShortCode": os.getenv("MPESA_SHORTCODE"),
        #     "Password": password,
        #     "Timestamp": timestamp,
        #     "TransactionType": "CustomerPayBillOnline",
        #     "Amount": int(amount),
        #     "PartyA": phone,
        #     "PartyB": os.getenv("MPESA_SHORTCODE"),
        #     "PhoneNumber": phone,
        #     "CallBackURL": os.getenv("MPESA_SHORTCODE"),
        #     "AccountReference": "LibraryFine",
        #     "TransactionDesc": "Library Fine Payment"
        # }
        token = get_access_token()
        if not token:
            return jsonify({"msg": "Failed to get M-Pesa access token"}), 500
        
        headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
        }
        print("Sending STK Push request to Safaricom")
        payload = build_stk_payload(phone, amount)
        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            headers=headers,
            json=payload
        )
        print("STK Push response: ", response.json())
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print("STK Error:", str(e))
        return jsonify({"msg": "An error occurred while initiating payment", "error": str(e)}), 500
    
@mpesa_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        print("Received M-Pesa Callback:", data)
        result = data.get('Body', {}).get('stkCallback', {})
        result_code = result.get('ResultCode')
        if result_code == 0:
            metadata = result.get('CallbackMetadata', {}).get('Item', [])
            amount = next((item['Value'] for item in metadata if item['Name'] == 'Amount'), None)
            phone = next((item['Value'] for item in metadata if item['Name'] == 'PhoneNumber'), None)

            if not phone or not amount:
                return jsonify({"msg": "Failed to retrieve phone number or amount from callback"}), 400
            
            user = User.query.filter_by(phone=phone).first()
            if not user:
                return jsonify({"msg": "User not found"}), 404
            unpaid_debts = Debt.query.filter_by(user_id=user.id, paid=False).all()
            if not unpaid_debts:
                return jsonify({"msg": "No unpaid debts found"}), 200
            for debt in unpaid_debts:
                debt.paid = True
            db.session.commit()

            try:
                receipt_path = generate_receipt_pdf(user, unpaid_debts, amount)
                send_email_with_attachment(
                    recipient=user.email,
                    subject="Library Receipt for Fine Payment",
                    body="Thank you for your payment. Find your receipt attached",
                    attachment_path=receipt_path
                )
            except Exception as e:
                print("Error sending receipt:", str(e))
                return jsonify({"msg": "Failed to send receipt"}), 400
            return jsonify({"msg": "Payment processed successfully"}), 200
        else:
            return jsonify({"msg": "Payment failed"}), 400
    except Exception as e:
        print("Error processing M-Pesa callback:", str(e))
        return jsonify({"msg": "An error occurred while processing M-Pesa callback"}), 500
        


            
