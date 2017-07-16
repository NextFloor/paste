from flask import Blueprint
from flask import jsonify, request

from models import db
from models import Paste


api = Blueprint('api', __name__)


@api.route('/new', methods=['POST'])
def post():
    paste = Paste(
        request.form['source'],
        request.form['highlight'],
        request.form['expiration'],
        request.form['title'],
        request.form['password'],
    )

    db.session.add(paste)
    db.session.commit()

    return jsonify(code=200, slug=paste.slug)


@api.route('/<slug>')
def view(slug):
    paste = Paste.get_or_404(slug)
    if paste.password:
        return jsonify(code=401)

    return jsonify(
        code=200,
        paste=dict(
            title=paste.title,
            source=paste.source,
            view_count=paste.view_count,
            created_at=int(paste.created_at.timestamp()),
            expire_at=int(paste.expire_at.timestamp()) if paste.expire_at else None,
            secret=paste.password is not None,
        ),
    )
