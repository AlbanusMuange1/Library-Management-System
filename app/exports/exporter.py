#!/usr/bin/env python3
import pandas as pd
from flask import send_file, jsonify
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def export_to_excel(data, columns, filename="export.xlsx"):
    try:
        if not data or not isinstance(data, list):
            return jsonify({"msg": "No data available to export"}), 400
        
        df = pd.DataFrame(data, columns=columns)
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)

        output.seek(0)
        return send_file(output, download_name=filename, as_attachment=True,  mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logger.exception('Error exporting data to Excel')
        return jsonify({'msg': 'Failed to export Excel file', 'error': str(e)}), 500
    
def export_to_csv(data, columns, filename="export.csv"):
    try:
        if not data or not isinstance(data, list):
            return jsonify({"msg": "No data available to export"}), 400
        
        df = pd.DataFrame(data, columns=columns)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(output, download_name=filename, as_attachment=True, mimetype='text/csv')
    
    except Exception as e:
        logger.exception('Error exporting data to CSV')
        return jsonify({'msg': 'Failed to export CSV file', 'error': str(e)}),
