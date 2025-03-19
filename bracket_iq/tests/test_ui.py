from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Tournament


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
        response = self.client.get(reverse("home"))

        # Check for the new welcome message
        self.assertContains(response, "Welcome to BracketIQ")
        self.assertContains(
            response, "Your intelligent March Madness bracket assistant"
        )

        # Check for the bracket container
        self.assertContains(response, '<div class="bracket-container">')

        # Check for seed list elements when they exist
        self.assertContains(response, f"Tournament {self.tournament.year}")
        self.assertContains(response, self.tournament.name)

        # Check for action buttons
        self.assertContains(response, "View Seeds")
        self.assertContains(response, "Delete")

    def test_home_page_empty_state(self):
        """Test the empty state of the home page when no seed lists exist."""
        # Delete the seed list created in setUp
        self.tournament.delete()

        response = self.client.get(reverse("home"))

        # Check for empty state message and call-to-action
        self.assertContains(response, "No seed lists have been created yet")
        self.assertContains(response, "Create Your First Seed List")

    def test_navigation_ui(self):
        """Test that our navigation bar is properly styled and contains all links."""
        response = self.client.get(reverse("home"))

        # Check for navigation container
        self.assertContains(response, "<nav>")
        self.assertContains(response, 'class="container"')

        # Check for all navigation links
        nav_links = [
            ("Home", reverse("home")),
            ("Profile", reverse("profile")),
            ("Create Bracket", reverse("create_bracket_form")),
            ("Create Live Bracket", reverse("create_live_bracket")),
        ]

        for link_text, link_url in nav_links:
            self.assertContains(response, f'href="{link_url}"')
            self.assertContains(response, link_text)

    def test_form_styling(self):
        """Test that our forms are properly styled with the new CSS classes."""
        response = self.client.get(reverse("register"))
        self.assertContains(response, 'class="form-container"')

        response = self.client.get(reverse("login"))
        self.assertContains(response, 'class="form-container"')

        response = self.client.get(reverse("create_seed_list"))
        self.assertContains(response, 'class="form-container"')

    def test_messages_styling(self):
        """Test that our flash messages are properly styled."""
        response = self.client.post(
            reverse("create_bracket_form"),
            {"tournament": self.tournament.id},
            follow=True,
        )

        # Check for message container and styling
        self.assertContains(response, 'class="messages"')
        self.assertContains(response, 'class="message message-success"')

    def test_navigation_links(self):
        """Test that navigation links are present and working"""
        links = [
            ("Home", reverse("home")),
            ("Profile", reverse("profile")),
            ("Create Bracket", reverse("create_bracket_form")),
            ("Create Live Bracket", reverse("create_live_bracket")),
        ]

        for name, url in links:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, name)
