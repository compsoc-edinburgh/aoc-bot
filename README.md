# AoC Bot

Can run on any server. Every year one volunteer runs it on their VPS.

Built with Poetry, so instructions are simplest with Poetry:

```
poetry install
poetry shell
python -m aoc_bot \
  --cache-file ./cache.json \ # cache to store updates
  --leaderboard-id 240997 \ # leaderboard ID on AoC
  --session-id "<AOC SESSION ID KEY>" \
  --slash-guild-id 123123123123 \ # Guild ID where slash command becomes active
  --discord-token "<DISCORD TOKEN>" \
  --mapping-file mapping.json \ # mapping store for username <-> Aoc Account
  --webhook-id "123123123123" \ # Webhook ID
  --webhook-token "<WEBHOOK TOKEN>" \
  --require-both-stars \
  # OPTIONAL --completion-role "<ROLE ID TO GIVE ON COMPLETION OF 25 DAYS>"
```

You can run without Poetry by installing any dependencies listed under [tool.poetry.dependencies] in pyproject.toml manually, then running the last command above  with your user/global Python installation.
