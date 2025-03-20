import datetime
import re

from django.contrib import admin, messages
from django.contrib.admin import AdminSite, SimpleListFilter
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.core.management import call_command, get_commands
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path
from django import forms

from .models import Tournament, Team, Game, Bracket, Prediction, BracketGame


class BracketIQAdminSite(AdminSite):
    site_header = "BracketIQ Administration"
    site_title = "BracketIQ Admin"
    index_title = "Tournament Management"
    index_template = "admin/bracketiq_admin/index.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "seed_tournament/",
                self.admin_view(self.seed_tournament_view),
                name="seed_tournament",
            ),
        ]
        return custom_urls + urls

    def seed_tournament_view(self, request):
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
        )

        # Dynamically discover available tournament seeding commands
        # Find all management commands
        available_years = []
        commands = get_commands()

        # Look for commands matching the pattern seed_tournament_YYYY
        for command_name in commands:
            match = re.match(r"seed_tournament_(\d{4})$", command_name)
            if match:
                year = match.group(1)
                available_years.append(int(year))

        # Sort years in descending order (newest first)
        available_years.sort(reverse=True)

        # If no years found, add current year as fallback
        if not available_years:
            current_year = datetime.datetime.now().year
            available_years = [current_year]

        context["years"] = available_years

        if request.method == "POST":
            year = request.POST.get("year")
            if not year:
                messages.error(request, "Year is required.")
                return redirect("admin:index")

            try:
                # Don't create the tournament here - let the management command handle it

                # Run seeding commands
                call_command("seed_teams")
                call_command(f"seed_tournament_{year}")

                return redirect("admin:index")

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                return TemplateResponse(
                    request, "admin/bracketiq_admin/seed_tournament.html", context
                )

        return TemplateResponse(
            request, "admin/bracketiq_admin/seed_tournament.html", context
        )


class GameForm(forms.ModelForm):
    """Custom form for Game model that limits winner choices to the two teams playing"""

    class Meta:
        model = Game
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If this is an existing game with both teams set, limit winner choices
        if (
            self.instance
            and self.instance.pk
            and self.instance.team1
            and self.instance.team2
        ):
            self.fields["winner"].queryset = Team.objects.filter(
                pk__in=[self.instance.team1.pk, self.instance.team2.pk]
            )
            self.fields["winner"].help_text = "Select the winner of this game."

            # Label score fields with team names
            self.fields["score1"].label = f"{self.instance.team1.name} Score"
            self.fields["score2"].label = f"{self.instance.team2.name} Score"
        else:
            self.fields["winner"].queryset = Team.objects.none()
            self.fields["winner"].help_text = (
                "Save the game with both teams first, then select a winner."
            )


class GameInline(admin.TabularInline):
    model = Game
    form = GameForm
    fields = (
        "round",
        "region",
        "game_number",
        "team1",
        "seed1",
        "score1",
        "team2",
        "seed2",
        "score2",
        "winner",
        "game_date",
    )
    readonly_fields = ("game_number",)
    extra = 0


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "start_date", "end_date", "games_completed")
    inlines = [GameInline]

    def games_completed(self, obj):
        completed_games = Game.objects.filter(
            tournament=obj, winner__isnull=False
        ).count()
        total_games = Game.objects.filter(tournament=obj).count()

        if total_games == 0:
            return "0%"

        completion_percentage = (completed_games / total_games) * 100
        return f"{completed_games}/{total_games} ({completion_percentage:.1f}%)"

    games_completed.short_description = "Games Completed"


class HasWinnerFilter(SimpleListFilter):
    title = "has winner"
    parameter_name = "has_winner"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(winner__isnull=False)
        if self.value() == "no":
            return queryset.filter(winner__isnull=True)
        return queryset


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameForm
    list_display = (
        "tournament",
        "round",
        "region",
        "game_number",
        "matchup",
        "score_display",
        "winner_display",
        "status",
        "game_date",
    )
    list_filter = ("tournament", "round", "region", HasWinnerFilter)
    search_fields = ("team1__name", "team2__name")
    readonly_fields = ("game_number",)
    actions = ["set_game_winner"]

    fieldsets = [
        (
            "Game Information",
            {
                "fields": [
                    "tournament",
                    "round",
                    "region",
                    "game_number",
                    "game_date",
                    "next_game",
                ],
            },
        ),
        (
            "Teams",
            {
                "fields": [("team1", "seed1", "score1"), ("team2", "seed2", "score2")],
            },
        ),
        (
            "Result",
            {
                "fields": ["winner"],
                "classes": ["wide"],
            },
        ),
    ]

    def matchup(self, obj):
        if obj.team1 and obj.team2:
            return f"({obj.seed1}) {obj.team1.name} vs ({obj.seed2}) {obj.team2.name}"
        if obj.team1:
            return f"({obj.seed1}) {obj.team1.name} vs TBD"
        if obj.team2:
            return f"TBD vs ({obj.seed2}) {obj.team2.name}"
        return "TBD"

    def score_display(self, obj):
        if obj.score1 is not None and obj.score2 is not None:
            return f"{obj.score1} - {obj.score2}"
        return "TBD"

    score_display.short_description = "Score"
    score_display.admin_order_field = "score1"

    def winner_display(self, obj):
        if obj.winner:
            return obj.winner.name
        return "TBD"

    winner_display.short_description = "Winner"
    winner_display.admin_order_field = "winner"

    def status(self, obj):
        if not obj.team1 or not obj.team2:
            return "Waiting for teams"
        if obj.winner:
            return "Completed"
        return "Needs winner"

    status.short_description = "Status"

    def set_game_winner(self, request, queryset):
        """Admin action to easily set game winners"""
        if "apply" not in request.POST:
            # Display the winner selection form
            valid_games = [game for game in queryset if game.team1 and game.team2]

            if not valid_games:
                self.message_user(
                    request,
                    "No valid games selected. Games must have both teams defined.",
                    messages.ERROR,
                )
                return None

            context = {
                "title": "Choose Game Winner",
                "queryset": valid_games,
                "action_checkbox_name": ACTION_CHECKBOX_NAME,
            }
            return render(
                request,
                "admin/bracketiq_admin/set_game_winner.html",
                context,
            )

        # Process the winner selection
        success_messages = []
        error_messages = []

        for game_id, winner_id in request.POST.items():
            if not game_id.startswith("winner_"):
                continue

            game_id = game_id.replace("winner_", "")
            if not winner_id:
                continue

            try:
                game = Game.objects.get(id=game_id)
                winner = Team.objects.get(id=winner_id)

                # Get scores if provided
                score1 = request.POST.get(f"score1_{game_id}")
                score2 = request.POST.get(f"score2_{game_id}")

                if score1 and score2:
                    try:
                        game.score1 = int(score1)
                        game.score2 = int(score2)
                    except ValueError:
                        error_messages.append(
                            f"Error processing game {game.game_number}: Invalid scores"
                        )
                        continue

                # Set winner and update the game
                game.winner = winner
                self._update_next_game(game, winner)
                game.save()

                # Update predictions for this game
                self._update_predictions(game)

                winner_name = winner.name
                success_messages.append(
                    f"Set {winner_name} as winner for Game {game.game_number}"
                )
            except (Game.DoesNotExist, Team.DoesNotExist, ValueError) as e:
                error_messages.append(f"Error processing game {game_id}: {str(e)}")

        # Display messages
        if success_messages:
            self.message_user(request, ", ".join(success_messages))
        if error_messages:
            self.message_user(request, ", ".join(error_messages), level=messages.ERROR)

        # Always return a response
        return None

    set_game_winner.short_description = "Set game winner"

    def _update_next_game(self, game, winner):
        """Helper method to update the next game with the winner of the current game."""
        if not game.next_game:
            return

        next_game = game.next_game
        seed = game.seed1 if winner == game.team1 else game.seed2

        if next_game.team1 is None:
            next_game.team1 = winner
            next_game.seed1 = seed
        else:
            next_game.team2 = winner
            next_game.seed2 = seed

        next_game.save()

    def _update_predictions(self, game):
        """Helper method to update predictions based on the game result."""
        if not game.winner:
            return

        # Update predictions for accuracy
        for prediction in Prediction.objects.filter(game=game):
            prediction.is_correct = prediction.predicted_winner == game.winner
            prediction.points_earned = prediction.calculate_points
            prediction.save()

    def save_model(self, request, obj, form, change):
        """
        When a game's winner is updated, update any games that this game
        feeds into, and update any predictions that were made on this game.
        """
        super().save_model(request, obj, form, change)

        # If the winner changed and this game feeds into another game
        if "winner" in form.changed_data and obj.next_game:
            self._update_next_game(obj, obj.winner)

        # If the winner changed, update predictions for this game
        if "winner" in form.changed_data and obj.winner:
            self._update_predictions(obj)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "mascot")
    search_fields = ("name",)


@admin.register(Bracket)
class BracketAdmin(admin.ModelAdmin):
    list_display = ("user", "tournament", "score", "created_at")
    list_filter = ("tournament",)
    search_fields = ("user__username",)


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "bracket",
        "game",
        "predicted_winner",
        "is_correct",
        "points_earned",
    )
    list_filter = ("bracket__tournament", "is_correct")
    search_fields = ("bracket__user__username",)
    readonly_fields = ("points_earned",)


@admin.register(BracketGame)
class BracketGameAdmin(admin.ModelAdmin):
    list_display = (
        "bracket_name",
        "bracket_user",
        "game",
        "matchup",
        "winner_display",
        "status",
        "updated_at",
    )
    list_filter = ("bracket__tournament", "game__round", "game__region")
    search_fields = (
        "bracket__name",
        "bracket__user__username",
        "team1__name",
        "team2__name",
    )
    readonly_fields = ("created_at", "updated_at")

    def bracket_name(self, obj):
        return obj.bracket.name

    bracket_name.short_description = "Bracket Name"
    bracket_name.admin_order_field = "bracket__name"

    def bracket_user(self, obj):
        return obj.bracket.user.username

    bracket_user.short_description = "User"
    bracket_user.admin_order_field = "bracket__user__username"

    fieldsets = [
        (
            "Bracket Information",
            {
                "fields": ["bracket", "game"],
            },
        ),
        (
            "Teams",
            {
                "fields": [("team1", "team1_seed"), ("team2", "team2_seed")],
            },
        ),
        (
            "Result",
            {
                "fields": ["winner"],
                "classes": ["wide"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    def matchup(self, obj):
        team1_name = obj.team1.name if obj.team1 else "TBD"
        team2_name = obj.team2.name if obj.team2 else "TBD"
        team1_seed = f"({obj.team1_seed})" if obj.team1_seed else ""
        team2_seed = f"({obj.team2_seed})" if obj.team2_seed else ""
        return f"{team1_seed} {team1_name} vs {team2_seed} {team2_name}"

    def winner_display(self, obj):
        if obj.winner:
            return obj.winner.name
        return "TBD"

    winner_display.short_description = "Winner"
    winner_display.admin_order_field = "winner"

    def status(self, obj):
        if not obj.team1 or not obj.team2:
            return "Waiting for teams"
        if obj.winner:
            return "Completed"
        return "In Progress"

    status.short_description = "Status"


# Create the custom admin site
admin_site = BracketIQAdminSite(name="bracketiq_admin")


# Register your models with the custom admin site
admin_site.register(Tournament, TournamentAdmin)
admin_site.register(Team, TeamAdmin)
admin_site.register(Game, GameAdmin)
admin_site.register(Bracket, BracketAdmin)
admin_site.register(Prediction, PredictionAdmin)
admin_site.register(BracketGame, BracketGameAdmin)
