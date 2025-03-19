from django.test import TestCase, Client
from django.contrib.auth import get_user_model


class AdminSiteTests(TestCase):
    """
    Test suite for the admin interface.
    """

    def setUp(self):
        self.client = Client()
        # Use get_user_model to avoid the imported-auth-user error
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        self.client.login(username="admin", password="adminpass123")
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="userpass123"
        )

    def test_admin_login(self):
        """Test admin login functionality."""
        # Logout first
        self.client.logout()

        # Try to access the admin index page - using the custom admin URL
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Login again
        logged_in = self.client.login(username="admin", password="adminpass123")
        self.assertTrue(logged_in)

        # Now should be able to access the admin index
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_tournament_management(self):
        """Test the tournament management page is accessible."""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        # Check for tournament management elements
        self.assertContains(response, "Tournament Management")
