from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class GenerateVisualisationForm(FlaskForm):
    """Form for generating a visualization."""
    title = StringField('Visualization Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description (Optional)', validators=[
        Length(max=500)
    ])
    # Chart type selection removed; Claude now selects visualization type autonomously.
    submit = SubmitField('Generate Visualization')

class ShareVisualisationForm(FlaskForm):
    """Form for sharing a visualization with another user."""
    user_id = SelectField('Share with User', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Share')