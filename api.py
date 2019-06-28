from flask import Blueprint
from flask import jsonify, request, url_for

from models import db
from models import Paste


api = Blueprint('api', __name__)


@api.route('/new', methods=['POST'])
def post():
    file = request.files['file']
    key = Paste.generate_random_resource_key()
    Paste.upload_file(key, file)

    paste = Paste(
        key,
        'text',
        request.form.get('expiration', 10080),
        request.form.get('title', file.filename),
        request.form.get('password'),
        True,
    )

    db.session.add(paste)
    db.session.commit()

    return jsonify(code=200, slug=paste.slug, url=url_for('view', slug=paste.slug, _external=True))


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
