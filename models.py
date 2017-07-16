import random
import string
from datetime import datetime, timedelta
from flask import abort
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import argon2
from pygments.lexers import guess_lexer
from sqlalchemy.sql import exists


db = SQLAlchemy()


class Paste(db.Model):
    __tablename__ = 'paste'
    slug = db.Column(db.String(4), primary_key=True)
    source = db.Column(db.Text, nullable=False)
    lexer = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(64))
    password = db.Column(db.String(128))
    view_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    expire_at = db.Column(db.DateTime)

    def __init__(self, source, highlight, expiration, title, password):
        expiration = int(expiration)

        if not source:
            raise ValueError()
        self.source = source
        if title:
            self.title = title
        if password:
            self.password = password
        if expiration > 0:
            self.expire_at = datetime.now() + timedelta(minutes=expiration)
        if highlight == 'auto':
            self.lexer = guess_lexer(source).aliases[0]
        else:
            self.lexer = highlight

        for _ in range(5):
            slug = self._generate_random_slug()
            if not db.session.query(exists().where(Paste.slug == slug)).scalar():
                self.slug = slug
                break
        else:
            raise RuntimeError()

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
    def _generate_random_slug():
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(4))
