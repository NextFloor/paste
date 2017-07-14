from datetime import datetime, timedelta
from flask import Flask, Response
from flask import abort, flash, redirect, render_template, session, url_for
from flask_humanize import Humanize
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters.html import HtmlFormatter
from sqlalchemy.exc import IntegrityError

from forms import PasteForm, PasswordForm
from models import db
from models import Paste


app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
db.init_app(app)
humanize = Humanize(app)


@humanize.localeselector
def get_locale():
    return 'ko_KR'


@app.before_first_request
def create_database():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def index():
    form = PasteForm()

    if form.validate_on_submit():
        paste = Paste()
        paste.source = form.source.data
        if form.highlighting.data == 'auto':
            paste.lexer = guess_lexer(form.source.data).aliases[0]
        else:
            paste.lexer = form.highlighting.data
        if form.title.data:
            paste.title = form.title.data
        if form.password.data:
            paste.password = form.password.data
        if int(form.expiration.data) > 0:
            paste.expire_at = datetime.now() + timedelta(minutes=int(form.expiration.data))

        while 1:
            try:
                paste.slug = Paste.generate_slug()
                db.session.add(paste)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
            else:
                break

        return redirect(url_for('view', slug=paste.slug))
    else:
        flash_errors(form)

    return render_template('index.html', form=form)


@app.route('/<slug>', methods=['GET', 'POST'])
def view(slug):
    paste = Paste.get_or_404(slug)
    if paste.password:
        form = PasswordForm()
        if form.validate_on_submit():
            if not paste.verify_password(form.password.data):
                flash('비밀번호가 일치하지 않습니다.', 'error')
                return render_template('password.html', form=form)
        else:
            flash_errors(form)
            return render_template('password.html', form=form)

    viewed = session.setdefault('viewed', [])
    if paste.slug not in viewed:
        viewed.append(paste.slug)
        session.permanent = True
        session.modified = True
        paste.view_count += 1
        db.session.add(paste)
        db.session.commit()

    lexer = get_lexer_by_name(paste.lexer)
    formatter = HtmlFormatter(
        linenos=True,
        linespans='line',
        lineanchors='line',
        anchorlinenos=True,
    )

    return render_template(
        'view.html',
        styles=formatter.get_style_defs(),
        highlighted_source=highlight(paste.source, lexer, formatter),
        lexer=lexer,
        paste=paste,
    )


@app.route('/<slug>/raw')
def view_raw(slug):
    paste = Paste.get_or_404(slug)
    if paste.password:
        abort(401)

    return Response(response=paste.source, status=200, mimetype='text/plain')


def flash_errors(form):
    for field, errors in form.errors.items():
        print(errors)
        for error in errors:
            flash('{} 입력칸에 다음과 같은 문제가 있습니다<br>{}'.format(getattr(form, field).label.text, error), 'error')