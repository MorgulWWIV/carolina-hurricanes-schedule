# NHL Team Schedule — NHL LED Scoreboard

A configurable plugin for the [**Falkyre NHL LED Scoreboard**](https://github.com/falkyre/nhl-led-scoreboard)

Choose any NHL team by its three-letter abbreviation and display that team's next games.

- Target: Falkyre 2026.03
- Matrix layout: 64x32
- Plugin ID: `nhl_team_schedule`
- Default team: Carolina Hurricanes (CAR)
- Display timezone: America/New_York (Eastern Time)
- Refresh interval: every 30 minutes
- Screen interval: 7 seconds per game
- Vertical transition: 0.8 seconds
- Data source: NHL public schedule API

## Choose your team

Edit `src/boards/plugins/nhl_team_schedule/config.json` and change `team_abbreviation` to the NHL club abbreviation you want. Examples:

| Team | Abbreviation |
|---|---|
| Carolina Hurricanes | CAR |
| Buffalo Sabres | BUF |
| New York Rangers | NYR |
| Boston Bruins | BOS |
| Toronto Maple Leafs | TOR |
| Edmonton Oilers | EDM |
| Vegas Golden Knights | VGK |

Use the NHL team's three-letter abbreviation. The heading on the display is generic: **UPCOMING GAMES**.

## Install

For a new installation:

```bash
python plugins.py add https://github.com/MorgulWWIV/nhl-scoreboard-schedule.git
```

For an existing installation, sync the updated plugin:

```bash
python plugins.py sync
```

Copy the sample configuration if you do not already have a config file:

```bash
cp src/boards/plugins/nhl_team_schedule/config.sample.json src/boards/plugins/nhl_team_schedule/config.json
```

Enable `nhl_team_schedule` in the scoreboard's state configuration if it is not already enabled, then restart:

```bash
sudo systemctl restart nhl-scoreboard
```

## Configuration

| Setting | Default | Purpose |
|---|---:|---|
| `team_abbreviation` | CAR | NHL team to display |
| `games_to_show` | 10 | Number of future games fetched |
| `display_seconds` | 7 | Seconds each game remains on screen |
| `scroll_seconds` | 0.8 | Duration of the vertical transition |
| `refresh_minutes` | 30 | Schedule refresh interval |
| `timezone` | America/New_York | Display timezone |

## Display behavior

The 64x32 display keeps **UPCOMING GAMES** fixed at the top. The matchup and local date/time scroll upward through the lower portion of the display. It shows one complete pass through the selected team's upcoming games, then returns control to Falkyre's board rotation.

A home game is shown as `TEAM vs OPP`; an away game is shown as `TEAM @ OPP`.

The plugin uses Python's standard library and does not require additional packages. It requires network access to the NHL public schedule API.
