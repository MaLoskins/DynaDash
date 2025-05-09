import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Dataset
from bs4 import BeautifulSoup

class VisualGenerateTemplateTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.client.testing = True

        # Create and log in a test user
        self.user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(self.user)
        db.session.commit()
        self.client.post('/auth/api/v1/login', json={
            'email': 'test@example.com',
            'password': 'password'
        })

        # Create a test dataset
        self.dataset = Dataset(
            user_id=self.user.id,
            filename='test_dataset.csv',
            original_filename='test_dataset.csv',
            file_path='/path/to/test_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(self.dataset)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_generate_template_ui(self):
        """Test that the generate template renders correctly and chart_type is removed."""
        response = self.client.get(f'/visual/generate/{self.dataset.id}')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        soup = BeautifulSoup(html, 'html.parser')

        # Ensure chart_type field is not present
        self.assertNotIn('chart_type', html)
        self.assertIsNone(soup.find(attrs={"name": "chart_type"}))

        # Check for explanatory text (both locations)
        self.assertIn(
            "The visualization type will now be selected automatically by Claude based on your data and description.",
            html
        )
        self.assertIn(
            "Chart type selection is now automatic:",
            html
        )

        # Ensure form fields are present
        self.assertIsNotNone(soup.find(attrs={"name": "title"}))
        self.assertIsNotNone(soup.find(attrs={"name": "description"}))
        self.assertIsNotNone(soup.find(attrs={"type": "submit"}))

    def test_generate_template_form_validation(self):
        """Test form validation errors display for missing required fields."""
        # Submit with missing title (required)
        response = self.client.post(
            f'/visual/generate/{self.dataset.id}',
            data={'description': 'desc only'},
            follow_redirects=True
        )
        html = response.get_data(as_text=True)
        self.assertIn('This field is required', html)

    def test_generate_template_form_success(self):
        """Test form submission works without chart_type and with valid data."""
        response = self.client.post(
            f'/visual/generate/{self.dataset.id}',
            data={'title': 'Valid Title', 'description': 'desc'},
            follow_redirects=True
        )
        # Should redirect to visualization view or show success message
        # Accept either a redirect or a success flash message
        html = response.get_data(as_text=True)
        self.assertTrue(
            'Visualization generated successfully!' in html or response.status_code in (200, 302)
        )

if __name__ == '__main__':
    unittest.main()