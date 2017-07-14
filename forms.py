from flask_wtf import FlaskForm
from pygments.lexers import get_all_lexers
from wtforms import SelectField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length


class PasteForm(FlaskForm):
    source = TextAreaField('내용', validators=[DataRequired()])
    title = StringField('제목 (선택)', validators=[Length(max=64)])
    password = PasswordField('비밀번호 (선택)')
    highlighting = SelectField('문법 강조', choices=[
            ('auto', '자동으로 문법 강조 선택'),
        ] + [(lexer[1][0], lexer[0]) for lexer in sorted(get_all_lexers())]
    )
    expiration = SelectField('자동 파기', choices=(
        ('0', '자동 파기 안 함'),
        ('1', '1분 뒤'),
        ('10', '10분 뒤'),
        ('60', '1시간 뒤'),
        ('1440', '1일 뒤'),
    ))


class PasswordForm(FlaskForm):
    password = PasswordField('비밀번호', validators=[DataRequired()])
