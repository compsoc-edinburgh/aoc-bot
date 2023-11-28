import argparse
import json
import threading

import aoc_bot.modules.leaderboard as leaderboard

import hikari
import tanjun

username_db_lock = threading.Lock()

component = tanjun.Component()

# This module provides slash commands for linking and unliking Discord IDs with
# Advent of Code User IDs. Linking isn't really beneficial right now except to
# show your name in notifications.
# e.g. "User #123 submitted!" vs "<@kilolympus> submitted!"
# Pings are disabled anyway, so this is a purely cosmetic aspect.


@component.with_slash_command
@tanjun.with_int_slash_option("aoc_id", "AoC User ID")
@tanjun.as_slash_command(
    "link_aoc",
    "Link your Advent of Code account to your Discord account",
    default_to_ephemeral=True,
)
async def link_command(
    ctx: tanjun.abc.Context,
    aoc_id: int,
    cli_args: argparse.Namespace = tanjun.inject(type=argparse.Namespace),
    bot: hikari.GatewayBot = tanjun.inject(type=hikari.GatewayBot),
) -> None:
    # Make sure no other threads modify content by acquiring a mutex
    # This is especially important since we separate the read and write operations.
    # There is no sufficient mode to open the file and do both reading (from
    # the top), writing (overwriting existing content), and creation if the file
    # doesn't exist.
    with username_db_lock:
        try:
            with open(cli_args.mapping_file, "r") as f:
                mapping: dict[str, str] = json.load(f)
        except FileNotFoundError as e:
            # If ia file is not found on open, proceed with empty and try to
            # create it later.
            mapping = {}
        except json.decoder.JSONDecodeError as e:
            # Failing to read a JSON could lead to data loss, so don't proceed.
            print(f"Failed link_command (read): {e}")
            await ctx.respond("Failed to link! Logs printed to console.")
            return

        mapping[str(aoc_id)] = str(ctx.author.id)

        try:
            # Attempt to retrieve the cached leaderboard, so we can check if
            # the user has a name on AoC. Also, it helps to check if they've
            # completed all 25 days.
            cached_leaderboard = leaderboard.retrieve_cached_leaderboard(cache_file=cli_args.cache_file)

            aoc_username = f"Anonymous User"
            if ("members" in cached_leaderboard and
                str(aoc_id) in cached_leaderboard["members"] and
                "name" in cached_leaderboard["members"][str(aoc_id)]):
                # If the user has a name, specify it for the notification, just
                # so they can double-check.
                aoc_username = cached_leaderboard["members"][str(aoc_id)]["name"]

            with open(cli_args.mapping_file, "w") as f:
                json.dump(
                    mapping,
                    f,
                    indent=2,  # Pretty-print it for easy of debugging
                )
                await ctx.respond(
                    f"Linked {ctx.author.username} with AoC User ID {str(aoc_id)} ({aoc_username})!"
                )

            # Now check if they have completed 25 days, 50 challenges
            # We can use the cached leaderboard, since if they issued /link
            # it's pretty much guaranteed their data's already been fetched
            # before. If it's not registered complete yet, it'll be triggered in
            # the next update anyway.
            events = leaderboard.get_leaderboard_set(
                cached_leaderboard,
                require_both=cli_args.require_both_stars,
            )
            if leaderboard.solved_all_days(events, str(aoc_id)):
                # Hide user ID at least on the public notification, but still
                # include the username since the final message itself doesn't
                # contain any identifying information.
                await leaderboard.send_webhook_notification(
                    bot,
                    f"{ctx.author.mention} linked their account.\n{leaderboard.display_final_message(cli_args.mapping_file, str(aoc_id), cli_args.completion_role)}",
                    webhook_id=cli_args.webhook_id,
                    webhook_token=cli_args.webhook_token,
                )
                await leaderboard.give_role(
                    bot=bot,
                    guild_id=cli_args.slash_guild_id,
                    mapping_file=cli_args.mapping_file,
                    member_id=str(aoc_id),
                    role_id=cli_args.completion_role,
                )

        except FileNotFoundError as e:
            # Either parent directory doesn't exist or no write perms?
            print(f"Failed link_command (write): {e}")
            await ctx.respond("Failed to link! Logs printed to console.")


@component.with_slash_command
@tanjun.as_slash_command(
    "unlink_aoc",
    "Unlink any Advent of Code account attached to your Discord account",
    default_to_ephemeral=True,
)
async def unlink_command(
    ctx: tanjun.abc.Context,
    cli_args: argparse.Namespace = tanjun.inject(type=argparse.Namespace),
) -> None:
    # Make sure no other threads are writing by acquiring a mutex

    with username_db_lock:
        try:
            with open(cli_args.mapping_file, "r") as f:
                mapping: dict[str, str] = json.load(f)
        except FileNotFoundError as e:
            # If ia file is not found on open, proceed with empty and try to
            # create it later.
            mapping = {}
        except json.decoder.JSONDecodeError as e:
            # Failing to read a JSON could lead to data loss, so don't proceed.
            print(f"Failed link_command (read): {e}")
            await ctx.respond("Failed to link! Logs printed to console.")
            return

        for aoc_id, discord_id in mapping.items():
            if discord_id == str(ctx.author.id):
                mapping.pop(aoc_id)
                break
        else:
            await ctx.respond("Your account wasn't linked in the first place!")
            # If there were no link, no need to write to file again
            return

        try:
            # Attempt to retrieve the cached leaderboard, so we can check if
            # the user has a name on AoC. Also, it helps to check if they've
            # completed all 25 days.
            cached_leaderboard = leaderboard.retrieve_cached_leaderboard(cache_file=cli_args.cache_file)

            aoc_username = f"Anonymous User"
            if ("members" in cached_leaderboard and
                str(aoc_id) in cached_leaderboard["members"] and
                "name" in cached_leaderboard["members"][str(aoc_id)]):
                # If the user has a name, specify it for the notification, just
                # so they can double-check.
                aoc_username = cached_leaderboard["members"][str(aoc_id)]["name"]

            with open(cli_args.mapping_file, "w") as f:
                json.dump(
                    mapping,
                    f,
                    indent=2,  # Pretty-print it for easy of debugging
                )
                await ctx.respond(
                    f"Unlinked {ctx.author.username} from AoC User ID {aoc_id} ({aoc_username})!"
                )

        except FileNotFoundError as e:
            # Either parent directory doesn't exist or no write perms
            print(f"Failed unlink_command (write): {e}")
            await ctx.respond("Failed to unlink! Logs printed to console.")


load_slash = component.make_loader()
