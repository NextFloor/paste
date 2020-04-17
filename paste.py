from flask import Flask, Response
from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_humanize import Humanize

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter

from api import api
from forms import PasteForm, PasswordForm
from models import db, boto3
from models import Paste


app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
app.config.from_object('config.development')
app.config.from_envvar('PASTE_SETTINGS', silent=True)
app.config['BOTO3_SERVICES'] = ['s3']
db.init_app(app)
boto3.init_app(app)
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
        source = form.source.data
        highlighting = form.highlighting.data
        resource = form.resource.data
        is_resource = False
        if resource:
            source = resource
            highlighting = 'text'
            is_resource = True

        paste = Paste(
            source,
            highlighting,
            form.expiration.data,
            form.title.data,
            form.password.data,
            is_resource
        )

        db.session.add(paste)
        db.session.commit()

        return redirect(url_for('view', slug=paste.slug))
    else:
        form.flash_errors()

    return render_template('index.html', form=form, js={
        'bucket_region': app.config['BOTO3_REGION'],
        'bucket_name': app.config['AWS_S3_BUCKET'],
        'identity_pool_id': app.config['AWS_COGNITO_IDENTITY_POOL'],
    })


@app.route('/<slug>', methods=['GET', 'POST'])
def view(slug):
    paste = Paste.get_or_404(slug)
    password = None
    if paste.password:
        form = PasswordForm()
        if form.validate_on_submit():
            if not paste.verify_password(form.password.data):
                flash('비밀번호가 일치하지 않습니다.', 'error')
                return render_template('password.html', form=form)
            password = form.password.data
        else:
            form.flash_errors()
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
        password=password,
    )


@app.route('/<slug>/raw', methods=['GET', 'POST'])
def view_raw(slug):
    paste = Paste.get_or_404(slug)
    if paste.password and not paste.verify_password(request.form.get('p', '')):
        abort(401)

    if paste.is_resource:
        return redirect(paste.generate_presigned_resource_url())

    return Response(response=paste.source, status=200, mimetype='text/plain')


@app.route('/x/k', methods=['POST'])
def generate_random_s3_key():
    key = Paste.generate_random_resource_key()
    return jsonify(key=key)
