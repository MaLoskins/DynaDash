import unittest
from flask import Flask
from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict

# Import the form to be tested
from app.blueprints.visual.forms import GenerateVisualisationForm

class TestGenerateVisualisationForm(unittest.TestCase):
    def setUp(self):
        # Flask-WTF requires an app context for CSRF and config
        self.app = Flask(__name__)
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.config['SECRET_KEY'] = 'test'
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_form_initialization_no_chart_type(self):
        """Form should not have a chart_type field (parameter dependency removed)."""
        form = GenerateVisualisationForm()
        self.assertFalse(hasattr(form, 'chart_type'), "chart_type field should not exist")

    def test_form_valid_with_required_title(self):
        """Form validates with only required title field."""
        formdata = MultiDict({'title': 'Test Visualization'})
        form = GenerateVisualisationForm(formdata)
        self.assertTrue(form.validate(), f"Form should validate with only title. Errors: {form.errors}")

    def test_form_valid_with_title_and_description(self):
        """Form validates with both title and optional description."""
        formdata = MultiDict({'title': 'Test Visualization', 'description': 'A sample description.'})
        form = GenerateVisualisationForm(formdata)
        self.assertTrue(form.validate(), f"Form should validate with title and description. Errors: {form.errors}")

    def test_form_invalid_without_title(self):
        """Form should not validate if title is missing."""
        formdata = MultiDict({'description': 'No title provided.'})
        form = GenerateVisualisationForm(formdata)
        self.assertFalse(form.validate(), "Form should not validate without title")
        self.assertIn('title', form.errors, "Missing title should produce a validation error")

    def test_form_no_validation_error_for_missing_chart_type(self):
        """Form should not error due to missing chart_type field."""
        formdata = MultiDict({'title': 'Test Visualization'})
        form = GenerateVisualisationForm(formdata)
        self.assertNotIn('chart_type', form.errors, "Form should not have chart_type validation errors")

    def test_form_rendering_fields(self):
        """Form renders only the expected fields."""
        form = GenerateVisualisationForm()
        rendered = str(form)
        self.assertIn('name="title"', rendered)
        self.assertIn('name="description"', rendered)
        self.assertIn('type="submit"', rendered)
        self.assertNotIn('name="chart_type"', rendered)

if __name__ == '__main__':
    unittest.main()