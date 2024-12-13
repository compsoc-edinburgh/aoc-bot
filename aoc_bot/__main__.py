import argparse

import hikari
import tanjun

parser = argparse.ArgumentParser()
parser.add_argument(
    "--cache-file",
    required=True,
    help="The path to a non-existent .json file which will be written to and read from for the cache.",
)
parser.add_argument(
    "--mapping-file",
    required=True,
    help="The path to a .json file which will be written to and read from for the username mapping.",
)
parser.add_argument(
    "--year",
    required=False,
    type=int,
    help="The year to hardcode to, mainly for debugging. Otherwise will always use the relevant year at time of leaderboard fetch (current year if December, previous year if any other month).",
)
parser.add_argument(
    "--leaderboard-id",
    required=True,
    type=int,
    help="The leaderboard ID. This is not the join code, but rather the integer ID shown in the URL.",
)
parser.add_argument(
    "--session-id",
    required=True,
    help="The ID value to use for the Session cookie when fetching the leaderboard.",
)
parser.add_argument(
    "--slash-guild-id",
    required=True,
    help="Guild ID where slash command should show up. This bot does not support global slash commands.",
)
parser.add_argument(
    "--webhook-id",
    required=True,
    type=int,
    help="The destination Discord webhook id (the snowflake in the webhook URL).",
)
parser.add_argument(
    "--webhook-token",
    required=True,
    help="The destination Discord webhook token (the last component of the webhook URL)",
)
parser.add_argument(
    "--discord-token",
    required=True,
    help="The token for the Discord bot to respond to slash commands.",
)
parser.add_argument(
    "--require-both-stars",
    action="store_true",
    help="If set, will only notify when users achieve both stars. Otherwise will notify for each one.",
)
parser.add_argument(
    "--completion-role",
    required=False,
    type=int,
    help="The green role to give upon completion. This role snowflake ID has to exist in the guild specified with --slash-guild-id.",
)


def main():
    args = parser.parse_args()
    bot = hikari.GatewayBot(
        token=args.discord_token,
        intents=hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.GUILD_MEMBERS,
    )

    (
        # Setting `declare_global_commands` to True will propagate commands globally,
        # which can take up to an hour to update. This bot only needs to work in one
        # server, so we specify that ID and in return get instant updates.
        tanjun.Client.from_gateway_bot(
            bot, declare_global_commands=[args.slash_guild_id]
        )
        .load_modules("aoc_bot.modules.link_command")
        .load_modules("aoc_bot.modules.leaderboard")
        .set_type_dependency(argparse.Namespace, args)
    )

    bot.run()


main()
