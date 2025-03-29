#!/usr/bin/env python3
from app.extensions import ma
from marshmallow import fields, validate

class BookSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    author = fields.Str(required=True, validate=validate.Length(min=1))
    category = fields.Str()
    total_copies = fields.Int(required=True, validate=validate.Range(min=1))
    available_copies = fields.Int(dump_only=True)
