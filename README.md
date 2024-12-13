# AoC Bot

![Screenshot](https://i.imgur.com/Rek8sAO.png)

Can run on any server. Every year one volunteer within CompSoc Discord's admin team tends to runs it on their VPS.

### Requirements

- Session cookie for AoC API access (the value after `session=` in browser's Cookie)
- A webhook ID and Token for the bot to send messages
- Bot needs to be added to the guild with slash command permissions
- Bot needs to have the Members intent enabled in the Discord developer console

The bot uses webhooks to send messages instead of Discord's native message-sending functionality, in order to spoof the username and display image. This means that this bot can run with any Bot token and it will function and look the same.

### Running

Built with Poetry, so instructions are simplest with Poetry. Poetry is a project-level package management tool for Python.

```bash
poetry install
poetry shell
python -m aoc_bot \
  --cache-file ./cache.json \
  --leaderboard-id 240997 \
  --session-id "<AOC SESSION ID KEY>" \
  --slash-guild-id 123123123123 \
  --discord-token "<DISCORD TOKEN>" \
  --mapping-file mapping.json \
  --webhook-id "123123123123" \
  --webhook-token "<WEBHOOK TOKEN>" \
  --require-both-stars
```

You can also run without Poetry by installing any dependencies listed under [tool.poetry.dependencies] in pyproject.toml manually, then running the last command above  with your user/global Python installation.

Some arguments explained:
- `--cache-file` is the cache file is stored for checking if a leaderboard changed (new star acquired by someone, new user, etc)
- `--leaderboard-id` is the AoC leaderboard ID
- `--session-id` is the alphanumerical AoC session cookie, which has access to the private leaderboard
- `--slash-guild-id` is the Discord server ID where slash commands become registered with
- `--mapping-file` is a JSON file keeping track of AoC username mappings to Discord IDs
- `--completion-role "123123"` is OPTIONAL, a role ID to give to people who completed all days of challenges
- `--year 2022` is OPTIONAL. By default, unless the current system month is November and December, it will check last year's data (so new year is handled out-of-the-box)
- `--require-both-stars` is OPTIONAL. By default, the bot will notify on every star which can be obnoxious if there are hundreds of people in the leaderboard. Adding this argument will only make it notify when users complete both parts of a day's problem.
