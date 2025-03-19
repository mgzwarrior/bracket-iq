import datetime
import re

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib import messages
from django.core.management import call_command, get_commands
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .models import Tournament, Team, Game, Bracket, Prediction


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


class GameInline(admin.TabularInline):
    model = Game
    fields = (
        "round",
        "region",
        "game_number",
        "team1",
        "team2",
        "winner",
        "score1",
        "score2",
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


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "tournament",
        "round",
        "region",
        "game_number",
        "matchup",
        "score_display",
        "winner_display",
        "game_date",
    )
    list_filter = ("tournament", "round", "region")
    search_fields = ("team1__name", "team2__name")
    readonly_fields = ("game_number",)

    def matchup(self, obj):
        if obj.team1 and obj.team2:
            return f"({obj.seed1}) {obj.team1.name} vs ({obj.seed2}) {obj.team2.name}"
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

    def save_model(self, request, obj, form, change):
        """
        When a game's winner is updated, update any games that this game
        feeds into, and update any predictions that were made on this game.
        """
        super().save_model(request, obj, form, change)

        # If the winner changed and this game feeds into another game
        if "winner" in form.changed_data and obj.next_game:
            # Update the next game with this winner
            next_game = obj.next_game
            if next_game.team1 is None:
                next_game.team1 = obj.winner
                next_game.seed1 = obj.seed1 if obj.winner == obj.team1 else obj.seed2
            else:
                next_game.team2 = obj.winner
                next_game.seed2 = obj.seed1 if obj.winner == obj.team1 else obj.seed2
            next_game.save()

            # Update predictions for accuracy
            for prediction in Prediction.objects.filter(game=obj):
                prediction.is_correct = prediction.predicted_winner == obj.winner
                prediction.save()


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


# Create the custom admin site
admin_site = BracketIQAdminSite(name="bracketiq_admin")


# Register your models with the custom admin site
admin_site.register(Tournament, TournamentAdmin)
admin_site.register(Team, TeamAdmin)
admin_site.register(Game, GameAdmin)
admin_site.register(Bracket, BracketAdmin)
admin_site.register(Prediction, PredictionAdmin)
