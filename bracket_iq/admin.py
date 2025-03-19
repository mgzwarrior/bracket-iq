from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.db import transaction
from django.template.response import TemplateResponse
from .models import Tournament, Team, Game, Bracket, Round, Region, Prediction
import re
import os
from django.conf import settings
from django.contrib.admin import AdminSite
from django.utils.html import format_html


class BracketIQAdminSite(AdminSite):
    site_header = "BracketIQ Administration"
    site_title = "BracketIQ Admin"
    index_title = "Tournament Management"
    index_template = "admin/bracketiq_admin/index.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "tournament/seed/",
                self.admin_view(self.seed_tournament_view),
                name="seed_tournament",
            ),
        ]
        return custom_urls + urls

    def seed_tournament_view(self, request):
        if request.method == "POST":
            year = request.POST.get("year")
            if not year:
                messages.error(request, "Year is required.")
                return redirect("admin:seed_tournament")

            try:
                # First transaction: Clean up existing data
                with transaction.atomic():
                    # Delete the tournaments for the given year
                    Tournament.objects.filter(year=year).delete()

                    # Clean up duplicate teams
                    team_names = Team.objects.values_list("name", flat=True).distinct()
                    for team_name in team_names:
                        teams = Team.objects.filter(name=team_name).order_by("id")
                        if teams.count() > 1:
                            # Keep the first one, delete the rest
                            first_team = teams.first()
                            Team.objects.filter(name=team_name).exclude(
                                id=first_team.id
                            ).delete()

                # Second transaction: Run seeding commands
                with transaction.atomic():
                    # Run the seeding commands
                    call_command("seed_teams")
                    call_command(f"seed_tournament_{year}")

                messages.success(request, f"Successfully seeded {year} tournament.")
                return redirect("admin:bracket_iq_tournament_changelist")
            except Exception as e:
                messages.error(request, f"Error seeding tournament: {str(e)}")
                return redirect("admin:seed_tournament")

        # GET request - show the form
        # Find all available tournament seeding scripts
        available_years = []
        commands_dir = os.path.join(
            settings.BASE_DIR, "bracket_iq", "management", "commands"
        )

        if os.path.exists(commands_dir):
            for filename in os.listdir(commands_dir):
                if filename.endswith(".py"):
                    match = re.match(r"seed_tournament_(\d{4})\.py", filename)
                    if match:
                        available_years.append(int(match.group(1)))

        available_years.sort(reverse=True)  # Show most recent years first

        if not available_years:
            messages.warning(request, "No tournament seeding scripts found.")
            return redirect("admin:index")

        context = {
            **self.each_context(request),
            "title": "Seed Tournament",
            "years": available_years,
        }
        return TemplateResponse(request, "admin/seed_tournament.html", context)


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
        total_games = obj.game_set.count()
        completed_games = obj.game_set.exclude(winner=None).count()
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            "green" if total_games == completed_games else "orange",
            completed_games,
            total_games,
            int((completed_games / total_games) * 100) if total_games > 0 else 0,
        )

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
        return f"{obj.team1.name if obj.team1 else 'TBD'} vs {obj.team2.name if obj.team2 else 'TBD'}"

    def score_display(self, obj):
        if obj.score1 is not None and obj.score2 is not None:
            return f"{obj.score1} - {obj.score2}"
        return "Not Played"

    score_display.short_description = "Score"

    def winner_display(self, obj):
        if not obj.winner:
            return format_html('<span style="color: orange;">Pending</span>')
        return format_html('<span style="color: green;">{}</span>', obj.winner.name)

    winner_display.short_description = "Winner"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.winner:
            # Update all predictions for this game
            predictions = Prediction.objects.filter(game=obj)
            for prediction in predictions:
                prediction.is_correct = prediction.predicted_winner == obj.winner
                prediction.save()

            # If this game has a next game, update the teams
            if obj.next_game:
                next_game = obj.next_game
                if (
                    next_game.team1 is None
                    or next_game.team1 == obj.team1
                    or next_game.team1 == obj.team2
                ):
                    next_game.team1 = obj.winner
                else:
                    next_game.team2 = obj.winner
                next_game.save()


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
@admin.register(Tournament, site=admin_site)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "start_date", "end_date")
    list_filter = ("year",)
    search_fields = ("name", "year")
    ordering = ("-year",)


@admin.register(Team, site=admin_site)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "mascot")
    search_fields = ("name", "short_name", "mascot")
    ordering = ("name",)


@admin.register(Game, site=admin_site)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "get_tournament_display",
        "get_round_display",
        "region",
        "game_number",
        "get_matchup_display",
    )
    list_filter = ("tournament__year", "round", "region")
    search_fields = ("team1__name", "team2__name", "tournament__name")
    ordering = ("tournament", "round", "game_number")

    def get_tournament_display(self, obj):
        return str(obj.tournament)

    get_tournament_display.short_description = "Tournament"
    get_tournament_display.admin_order_field = "tournament"

    def get_round_display(self, obj):
        try:
            return Round.from_value(obj.round).label
        except ValueError:
            return "Unknown Round"

    get_round_display.short_description = "Round"
    get_round_display.admin_order_field = "round"

    def get_matchup_display(self, obj):
        team1_name = obj.team1.name if obj.team1 else "TBD"
        team2_name = obj.team2.name if obj.team2 else "TBD"
        return f"({obj.seed1}) {team1_name} vs ({obj.seed2}) {team2_name}"

    get_matchup_display.short_description = "Matchup"


@admin.register(Bracket, site=admin_site)
class BracketAdmin(admin.ModelAdmin):
    list_display = ("name", "get_tournament_display", "user", "score", "created_at")
    list_filter = ("tournament__year", "user")
    search_fields = ("name", "user__username", "tournament__name")
    ordering = ("-created_at",)

    def get_tournament_display(self, obj):
        return str(obj.tournament)

    get_tournament_display.short_description = "Tournament"
    get_tournament_display.admin_order_field = "tournament"
