import argparse
import json
import threading

import tanjun

username_db_lock = threading.Lock()

# Create the component.
# Template courtesy of https://github.com/parafoxia/hikari-intro
component = tanjun.Component()


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
            with open(cli_args.mapping_file, "w") as f:
                json.dump(
                    mapping,
                    f,
                    indent=2,  # Pretty-print it for easy of debugging
                )
                await ctx.respond(
                    f"Linked {ctx.author.username} with AoC User ID {str(aoc_id)}!"
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
            with open(cli_args.mapping_file, "w") as f:
                json.dump(
                    mapping,
                    f,
                    indent=2,  # Pretty-print it for easy of debugging
                )
                await ctx.respond(
                    f"Unlinked {ctx.author.username} from AoC User ID {aoc_id}!"
                )

        except FileNotFoundError as e:
            # Either parent directory doesn't exist or no write perms
            print(f"Failed unlink_command (write): {e}")
            await ctx.respond("Failed to unlink! Logs printed to console.")


load_slash = component.make_loader()
