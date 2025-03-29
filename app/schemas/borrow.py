#!/usr/bin/env python3
from app.extensions import ma
from marshmallow import fields

class BorrowSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    book_id = fields.Int(required=True)
    borrow_date = fields.Date()
    due_date = fields.Date()
    return_date = fields.Date(allow_none=True)
    fine = fields.Float()
    returned = fields.Boolean()
