"""Carolina Hurricanes upcoming schedule board for NHL LED Scoreboard."""

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
    """Scroll vertically through the next several Carolina Hurricanes games."""

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
        self.team_abbreviation = self.board_config.get("team_abbreviation", "CAR")
        self.show_venue = bool(self.board_config.get("show_venue", False))

        self.font = data.config.layout.font
        self.font_large = data.config.layout.font_large
        self._games = []
        self._last_refresh = 0
        self._error = None
        self._game_index = 0

    def _fetch_games(self):
        """Fetch and normalize future games from the NHL schedule API."""
        url = SCHEDULE_URL.format(team=self.team_abbreviation)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NHL-LED-Scoreboard-Carolina-Schedule/1.0"}
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
            start_utc = datetime.datetime.fromisoformat(
                start_text.replace("Z", "+00:00")
            )
            if start_utc <= now_utc:
                continue

            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})
            is_home = home.get("abbrev") == self.team_abbreviation
            opponent = away if is_home else home
            opponent_abbrev = opponent.get("abbrev", "TBD")
            local_start = start_utc.astimezone(local_tz)

            games.append({
                "start": start_utc,
                "matchup": (
                    f"{self.team_abbreviation} vs {opponent_abbrev}"
                    if is_home else
                    f"{self.team_abbreviation} @ {opponent_abbrev}"
                ),
                "date_time": local_start.strftime("%b %d  %I%p").replace(" 0", " ").replace("  ", " "),
                "venue": game.get("venue", {}).get("default", "")
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
            debug.info("Carolina schedule refreshed: %d upcoming games", len(self._games))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            self._error = str(exc)
            debug.warning("Unable to refresh Carolina schedule: %s", exc)
        finally:
            self._last_refresh = now

    def _draw_card(self, layout, game, vertical_offset=0):
        """Draw the existing three-line layout shifted vertically by pixel offset."""
        lines = (
            ("title", "CANES SCHEDULE", "red"),
            ("matchup", game["matchup"], "white"),
            ("date_time", game["date_time"], "cyan"),
        )

        for key, value, color in lines:
            if layout and key in layout:
                item = layout[key]
                position = self.matrix.layout_position(item)
                position = (position[0], position[1] + vertical_offset)
                self.matrix.draw_text(
                    position,
                    value,
                    font=item.font,
                    fill=color,
                    align=item.align
                )
            else:
                y_positions = {"title": 6, "matchup": 17, "date_time": 28}
                font = self.font_large if key == "matchup" else self.font
                self.matrix.draw_text_centered(
                    y_positions[key] + vertical_offset, value, font, color
                )

    def _scroll_to_next_game(self, layout, current_game, next_game):
        """Slide the current three-line screen up as the next screen enters below."""
        height = self.display_height
        steps = max(1, height)
        frame_delay = self.scroll_seconds / steps

        for step in range(1, steps + 1):
            if self.sleepEvent.is_set():
                return False

            offset = round(height * step / steps)
            self.matrix.clear()
            self._draw_card(layout, current_game, -offset)
            self._draw_card(layout, next_game, height - offset)
            self.matrix.render()

            if self.sleepEvent.wait(frame_delay):
                return False

        return True

    def render(self):
        self._refresh_if_needed()
        layout = self.get_board_layout("carolina_schedule")

        if self._error and not self._games:
            self.matrix.clear()
            self._draw_status(layout, "DATA UNAVAILABLE", "CHECK NETWORK")
            self.matrix.render()
            self.sleepEvent.wait(self.display_seconds)
            return

        if not self._games:
            self.matrix.clear()
            self._draw_status(layout, "NO UPCOMING GAMES", "SCHEDULE CLEAR")
            self.matrix.render()
            self.sleepEvent.wait(self.display_seconds)
            return

        current_index = self._game_index % len(self._games)
        current_game = self._games[current_index]

        self.matrix.clear()
        self._draw_card(layout, current_game)
        self.matrix.render()

        if self.sleepEvent.wait(self.display_seconds):
            return

        if len(self._games) > 1:
            next_index = (current_index + 1) % len(self._games)
            next_game = self._games[next_index]
            if self._scroll_to_next_game(layout, current_game, next_game):
                self._game_index = next_index

    def _draw_status(self, layout, matchup, date_time):
        """Draw the normal heading and status text when no schedule is available."""
        self._draw_card(
            layout,
            {"matchup": matchup, "date_time": date_time}
        )
