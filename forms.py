from flask import flash
from flask_wtf import FlaskForm
from pygments.lexers import get_all_lexers
from wtforms import SelectField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length


class ErrorFlashMixin:
    def flash_errors(self):
        for field, errors in self.errors.items():
            for error in errors:
                flash('{} 입력칸에 다음과 같은 문제가 있습니다<br>{}'.format(getattr(self, field).label.text, error), 'error')


class PasteForm(ErrorFlashMixin, FlaskForm):
    source = TextAreaField('내용', validators=[DataRequired()])
    title = StringField('제목 (선택)', validators=[Length(max=64)])
    password = PasswordField('비밀번호 (선택)')
    highlighting = SelectField('문법 강조', choices=[
            ('auto', '자동으로 문법 강조 선택'),
        ] + [(lexer[1][0], lexer[0]) for lexer in sorted(get_all_lexers())]
    )
    expiration = SelectField('자동 파기', choices=(
        ('-1', '자동 파기 안 함'),
        ('1', '1분 뒤'),
        ('10', '10분 뒤'),
        ('60', '1시간 뒤'),
        ('1440', '1일 뒤'),
    ))


class PasswordForm(ErrorFlashMixin, FlaskForm):
    password = PasswordField('비밀번호', validators=[DataRequired()])
