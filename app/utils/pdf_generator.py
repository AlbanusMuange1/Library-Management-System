#!/usr/bin/env python3
from fpdf import FPDF
import os
import datetime
import logging

os.makedirs("logs", exist_ok=True)

logging.basicConfig(filename='logs/pdf_errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')

def generate_receipt_pdf(user, debts, amount_paid):
    try:
        if not user or not debts:
            raise ValueError('User or debts information missing')
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size = 15)

        pdf.cell(200, 10, txt="Library Payment Receipts", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Name: {user.name}", ln=True)
        pdf.cell(200, 10, txt=f"Email: {user.email}", ln=True)
        pdf.cell(200, 10, txt=f"Amount Paid: KES {amount_paid:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Cleared Debt:", ln=True)
        for d in debts:
            title = d.book.title if d.book else "Unknown Book"
            amount = d.fine_amount if d.fine_amount else 0.0
            pdf.cell(200,10, txt=f"{title} - KES {amount:.2f}", ln=True)

        receipt_dir = "receipts"
        os.makedirs(receipt_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        path = os.path.join(receipt_dir, f"receipt_{user.id}_{timestamp}.pdf")
        pdf.output(path)
        return path
    except Exception as e:
        logging.error(f"Error generating receipt PDF: {str(e)}", exc_info=True)
        return None
    