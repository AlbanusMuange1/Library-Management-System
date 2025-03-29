#!/usr/bin/env python3
from app.extensions import ma
from marshmallow import fields, validate

class UserSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    role = fields.Str(validate=validate.OneOf(["member", "librarian", "admin"]))
