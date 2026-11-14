# Carolina Hurricanes Schedule — NHL LED Scoreboard

A plugin for the **Falkyre NHL LED Scoreboard** that displays the next 10 Carolina Hurricanes games, rotating one game per screen.

- Target: Falkyre 2026.03
- Matrix layout: 64x32
- Team: Carolina Hurricanes (CAR)
- Display timezone: America/New_York (Eastern Time)
- Refresh interval: every 30 minutes
- Screen interval: 7 seconds
- Data source: NHL public schedule API

## Install

From the NHL LED Scoreboard application directory, run:

```bash
python plugins.py add https://github.com/MorgulWWIV/carolina-hurricanes-schedule.git
```

Then copy the sample configuration:

```bash
cp src/boards/plugins/carolina_schedule/config.sample.json src/boards/plugins/carolina_schedule/config.json
```

Enable the board by adding `carolina_schedule` to the states list in `config/config.json` (alongside the other board IDs). Follow the project's plugin documentation for the exact state configuration used by your installation.

Restart the scoreboard service:

```bash
sudo systemctl restart nhl-scoreboard
```

## Configuration

Edit `src/boards/plugins/carolina_schedule/config.json`:

| Setting | Default | Purpose |
|---|---:|---|
| `games_to_show` | 10 | Number of future games fetched |
| `display_seconds` | 7 | Seconds per game screen |
| `refresh_minutes` | 30 | Schedule refresh interval |
| `timezone` | America/New_York | Display timezone |
| `team_abbreviation` | CAR | NHL team abbreviation |
| `show_venue` | false | Reserved for a future venue display option |

The plugin uses Python's standard library and does not require additional packages.

## Display

Each 64x32 screen uses the small font for all three lines to keep text within the panel. It shows `CANES SCHEDULE`, the matchup, and a compact local date/time (for example, `Nov 15 7PM`). A home game is shown as `CAR vs OPP`; an away game is shown as `CAR @ OPP`.

## Notes

The plugin obtains the schedule from the NHL's public web API. It requires network access from the scoreboard computer. This code is written against the Falkyre plugin/board interface and has not been physically tested on your LED matrix; please verify rendering on the scoreboard after installation.
