"""Configurable NHL team schedule board for NHL LED Scoreboard."""

import datetime
import json
import logging
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

from boards.base_board import BoardBase
from . import __version__, __description__, __board_name__

debug = logging.getLogger("scoreboard")
SCHEDULE_URL = "https://api-web.nhle.com/v1/club-schedule-season/{team}/now"


class CarolinaScheduleBoard(BoardBase):
    """Keep a generic heading fixed while the selected team games scroll upward."""

    def __init__(self, data, matrix, sleepEvent):
        super().__init__(data, matrix, sleepEvent)
        self.board_name = __board_name__
        self.board_version = __version__
        self.board_description = __description__

        self.games_to_show = int(self.board_config.get("games_to_show", 10))
        self.display_seconds = int(self.board_config.get("display_seconds", 7))
        self.refresh_seconds = int(self.board_config.get("refresh_minutes", 30)) * 60
        self.scroll_seconds = float(self.board_config.get("scroll_seconds", 0.8))
        self.timezone_name = self.board_config.get("timezone", "America/New_York")
        self.team_abbreviation = str(self.board_config.get("team_abbreviation", "CAR")).strip().upper()

        self.font = data.config.layout.font
        self.font_large = data.config.layout.font_large
        self._games = []
        self._last_refresh = 0
        self._error = None
        self._game_index = 0

    def _fetch_games(self):
        url = SCHEDULE_URL.format(team=self.team_abbreviation)
        request = urllib.request.Request(
            url, headers={"User-Agent": "NHL-LED-Scoreboard-Team-Schedule/1.0"}
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        local_tz = ZoneInfo(self.timezone_name)
        games = []
        for game in payload.get("games", []):
            start_text = game.get("startTimeUTC")
            if not start_text:
                continue
            start_utc = datetime.datetime.fromisoformat(start_text.replace("Z", "+00:00"))
            if start_utc <= now_utc:
                continue

            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})
            is_home = home.get("abbrev") == self.team_abbreviation
            opponent = away if is_home else home
            local_start = start_utc.astimezone(local_tz)
            games.append({
                "start": start_utc,
                "matchup": (
                    f"{self.team_abbreviation} vs {opponent.get('abbrev', 'TBD')}"
                    if is_home else
                    f"{self.team_abbreviation} @ {opponent.get('abbrev', 'TBD')}"
                ),
                "date_time": local_start.strftime("%b %d  %I%p").replace(" 0", " ").replace("  ", " "),
            })

        games.sort(key=lambda item: item["start"])
        return games[:max(1, self.games_to_show)]

    def _refresh_if_needed(self):
        now = time.time()
        if self._games and now - self._last_refresh < self.refresh_seconds:
            return
        if not self._games and self._last_refresh and now - self._last_refresh < 60:
            return
        try:
            self._games = self._fetch_games()
            self._error = None
            self._game_index = 0
            debug.info("%s schedule refreshed: %d upcoming games", self.team_abbreviation, len(self._games))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            self._error = str(exc)
            debug.warning("Unable to refresh %s schedule: %s", self.team_abbreviation, exc)
        finally:
            self._last_refresh = now

    def _layout_item(self, layout, key):
        return layout[key] if layout and key in layout else None

    def _draw_heading(self, layout):
        """Draw the fixed heading above the scrolling game area."""
        title = "TEAM GAMES"
        item = self._layout_item(layout, "title")
        if item:
            self.matrix.draw_text_layout(item, title, fillColor="red")
        else:
            self.matrix.draw_text_centered(6, title, self.font, "red")

    def _draw_game_details(self, layout, game, offset=0):
        """Draw just the matchup and date lines at a vertical offset."""
        for key, value, color, fallback_y in (
            ("matchup", game["matchup"], "white", 17),
            ("date_time", game["date_time"], "cyan", 28),
        ):
            item = self._layout_item(layout, key)
            if item:
                position = self.matrix.layout_position(item)
                self.matrix.draw_text(
                    (position[0], position[1] + offset),
                    value,
                    font=item.font,
                    fill=color,
                    align=item.align,
                )
            else:
                self.matrix.draw_text_centered(
                    fallback_y + offset, value, self.font, color
                )

    def _draw_fixed_heading_over_scroll(self, layout):
        """Mask any scrolling pixels from the heading band, then redraw its label."""
        self.matrix.draw_rectangle((0, 0), (self.display_width, 11), fill=(0, 0, 0))
        self._draw_heading(layout)

    def _scroll_to_next_game(self, layout, current_game, next_game):
        """Move game details up through the lower panel while the heading stays still."""
        panel_height = max(1, self.display_height - 11)
        steps = panel_height
        frame_delay = self.scroll_seconds / steps

        for step in range(1, steps + 1):
            if self.sleepEvent.is_set():
                return False
            offset = round(panel_height * step / steps)
            self.matrix.clear()
            self._draw_game_details(layout, current_game, -offset)
            self._draw_game_details(layout, next_game, panel_height - offset)
            self._draw_fixed_heading_over_scroll(layout)
            self.matrix.render()
            if self.sleepEvent.wait(frame_delay):
                return False
        return True

    def _draw_status(self, layout, matchup, date_time):
        self.matrix.clear()
        self._draw_heading(layout)
        self._draw_game_details(layout, {"matchup": matchup, "date_time": date_time})
        self._draw_fixed_heading_over_scroll(layout)

    def render(self):
        """Show one complete pass through the upcoming games, then yield to Falkyre."""
        layout = self.get_board_layout("carolina_schedule")
        self._refresh_if_needed()

        if self._error and not self._games:
            self._draw_status(layout, "DATA UNAVAILABLE", "CHECK NETWORK")
            self.matrix.render()
            self.sleepEvent.wait(self.display_seconds)
            return

        if not self._games:
            self._draw_status(layout, "NO UPCOMING GAMES", "SCHEDULE CLEAR")
            self.matrix.render()
            self.sleepEvent.wait(self.display_seconds)
            return

        # Capture this pass so refreshes or index changes cannot extend it endlessly.
        games_this_pass = list(self._games)
        total_games = len(games_this_pass)

        for index, current_game in enumerate(games_this_pass):
            if self.sleepEvent.is_set():
                return

            self.matrix.clear()
            self._draw_heading(layout)
            self._draw_game_details(layout, current_game)
            self._draw_fixed_heading_over_scroll(layout)
            self.matrix.render()

            # Give each game its full screen time, including the final game.
            if self.sleepEvent.wait(self.display_seconds):
                return

            # Scroll to the next game, but do not wrap after the final game.
            if index < total_games - 1:
                next_game = games_this_pass[index + 1]
                if not self._scroll_to_next_game(layout, current_game, next_game):
                    return

        # Reset for the next time Falkyre selects this board.
        self._game_index = 0
        debug.info("%s schedule: completed one pass through %d games", self.team_abbreviation, total_games)
