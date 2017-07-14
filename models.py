import random
import string
from datetime import datetime
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import argon2


db = SQLAlchemy()


class Paste(db.Model):
    __tablename__ = 'paste'
    slug = db.Column(db.String(4), primary_key=True)
    source = db.Column(db.Text, nullable=False)
    lexer = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(64))
    password = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.now)
    expire_at = db.Column(db.DateTime)

    @db.validates('password')
    def _validate_password(self, key, password):
        return argon2.hash(password)

    def verify_password(self, password):
        return (not self.password) or argon2.verify(password, self.password)

    @classmethod
    def get_or_404(cls, slug):
        paste = Paste.query.get_or_404(slug)
        if paste.expire_at and (paste.expire_at <= datetime.now()):
            db.session.delete(paste)
            db.session.commit()
            abort(404)

        return paste

    @staticmethod
    def generate_slug():
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(4))
