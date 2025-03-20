from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from ..models import Tournament, Bracket

User = get_user_model()


class UITests(TestCase):
    """
    Test suite for our UI components - ensuring our bracket interface
    is as smooth as a perfect jump shot!
    """

    def setUp(self):
        """Set up our testing environment with a user and some sample data."""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.tournament = Tournament.objects.create(
            year=2024,
            name="NCAA March Madness",
            start_date="2024-03-19",
            end_date="2024-04-08",
        )
        self.client.login(username="testuser", password="12345")

    def test_home_page_ui_elements(self):
        """Test that our home page has all the required UI elements."""
        # Create a bracket for testing
        Bracket.objects.create(
            user=self.user, tournament=self.tournament, name="Test Bracket 2024"
        )

        response = self.client.get(reverse("home"))

        # Check for the welcome message
        self.assertContains(response, "Welcome to BracketIQ")
        self.assertContains(
            response, "Your intelligent March Madness bracket assistant"
        )

        # Check for the tournament container
        self.assertContains(response, '<div class="bracket-container">')

        # Check for tournament elements when they exist
        self.assertContains(response, "NCAA March Madness")
        self.assertContains(response, "2024")

        # Check for bracket elements in the correct order
        self.assertContains(response, "<h3>Test Bracket 2024</h3>")
        self.assertContains(response, "<p>NCAA March Madness</p>")

        # Check for the create bracket link
        self.assertContains(response, "Create Bracket")

    def test_home_page_empty_state(self):
        """Test the empty state of the home page when no tournaments exist."""
        # Delete ALL tournaments to ensure empty state
        Tournament.objects.all().delete()

        response = self.client.get(reverse("home"))

        # Check for empty state message
        self.assertContains(response, "No tournaments are available yet")

    def test_navigation_ui(self):
        """Test that our navigation bar is properly styled and contains all links."""
        response = self.client.get(reverse("home"))

        # Check for navigation container
        self.assertContains(response, "<nav>")
        self.assertContains(response, 'class="container"')

        # Check for all navigation links
        nav_links = [
            ("Home", "/"),
            ("Profile", "/accounts/profile/"),
            ("Create Bracket", "/bracket/create/"),
        ]

        for link_text, link_url in nav_links:
            self.assertContains(response, f'href="{link_url}"')
            self.assertContains(response, link_text)

    def test_form_styling(self):
        """Test that our forms are properly styled with appropriate elements."""
        response = self.client.get(reverse("login"))

        # Check for form elements
        self.assertContains(response, "<form")
        self.assertContains(response, 'type="submit"')

        # Create bracket form
        response = self.client.get(reverse("create_bracket_form"))
        self.assertContains(response, "<form")
        self.assertContains(response, 'type="submit"')

    def test_messages_styling(self):
        """Test that our flash messages work properly."""
        # Create a bracket and then try to access it
        bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament, name="Test Bracket"
        )

        # Delete the bracket - this should trigger a success message
        response = self.client.post(
            reverse("delete_bracket", args=[bracket.pk]), follow=True
        )

        # Check the response status and redirects
        self.assertEqual(response.status_code, 200)

        # Check for messages in the context
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)

    def test_bracket_display(self):
        """Test that bracket display page URL pattern works correctly"""
        # Create a bracket for testing
        bracket = Bracket.objects.create(
            user=self.user, tournament=self.tournament, name="Test Bracket"
        )

        # Get the URL for the bracket display page
        url = reverse("display_bracket", args=[bracket.pk])

        # Verify the URL pattern is correct
        self.assertTrue(url.startswith("/bracket/"))
        self.assertTrue(str(bracket.pk) in url)
