from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired

class UploadDatasetForm(FlaskForm):
    """Form for uploading a dataset."""
    file = FileField('Dataset File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'json'], 'Only CSV and JSON files are allowed.')
    ])
    is_public = BooleanField('Make this dataset public')
    submit = SubmitField('Upload Dataset')

class ShareDatasetForm(FlaskForm):
    """Form for sharing a dataset with another user."""
    user_id = SelectField('Share with User', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Share')