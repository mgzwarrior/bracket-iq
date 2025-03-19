from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminSiteTests(TestCase):
    """
    Test suite for the admin interface.
    """

    def setUp(self):
        self.client = Client()
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
        
        # Try to access the admin index page
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login again
        logged_in = self.client.login(username="admin", password="adminpass123")
        self.assertTrue(logged_in)
        
        # Now should be able to access the admin index
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    def test_users_listed(self):
        """Test that users are listed on user admin page."""
        response = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin_user.username)
        self.assertContains(response, self.regular_user.username) 