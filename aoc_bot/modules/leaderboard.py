# Original Source:
# Advent of code leaderboard notifier (MIT, Dec 2020, tofran)
# https://github.com/tofran/advent-of-code-leaderboard-notifier
#
#
# Modifications by Yuto Takano under MIT license
#
import argparse
import json
from datetime import date, datetime
import os
from typing import Any, Optional, Set, Tuple

import hikari
import requests
import tanjun

# Create the component.
# Template courtesy of https://github.com/parafoxia/hikari-intro
component = tanjun.Component()


def get_default_year() -> int:
    """Get the current year.

    Returns
    -------
    int
        The common calendar year in 4 digits.
    """
    today = date.today()

    # Return previous year if we're not in December
    if today.month != 12:
        return today.year - 1

    return today.year


def retrieve_cached_leaderboard(cache_file: str) -> Any:
    """Retrieve the cached leaderboard JSON from disk.

    Returns
    -------
    Any
        The parsed JSON response for the previous request.
    """
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cached_leaderboard(data: Any, cache_file: str) -> None:
    """Save the leadeboard JSON to disk.

    Parameters
    ----------
    data : Any
        The parsed JSON response for a request.
    """
    with open(cache_file, "w+") as f:
        json.dump(
            data,
            f,
            indent=2,  # Pretty-print it for easy of debugging
        )


def fetch_leaderboard(
    leaderboard_id: int, session_id: str, year: Optional[int] = None
) -> Any:
    """Query the leaderboard endpoint and return the parsed JSON response.

    Returns
    -------
    Any
        The parsed JSON response for a request.
    """
    if year is None:
        year = get_default_year()

    response = requests.get(
        f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json",
        cookies={"session": session_id},
    )

    response.raise_for_status()

    return response.json()


def get_leaderboard_set(
    leaderboard: Any, require_both: bool = True
) -> Set[Tuple[str, str, str]]:
    """Create the set of member-day-part tuples for completions.

    Parameters
    ----------
    leaderboard : Any
        The parsed leaderboard JSON.
    require_both : bool
        Whether to return only tuples where the member completed both challenges
        for a given day. Defaults to True. If this is False, event notifications
        for both Part 1 and Part 2 completions will be sent. If this is True,
        notifications will only be sent on Part 2 completion

    Returns
    -------
    Set[Tuple[str, str, str]]
        A tuple of the AoC member ID, day number, and completion part.
    """
    return set(
        (member_id, day, part)
        for member_id, member in leaderboard.get("members", {}).items()
        for day, exercises in member.get("completion_day_level", {}).items()
        for part in exercises.keys()
        if (require_both and part == "2") or not require_both
    )


async def send_webhook_notification(
    bot: hikari.GatewayBot,
    content: str,
    webhook_id: int,
    webhook_token: str,
    max_content_len: int = 2000,
):
    """Execute the webhook with the sepcified content.

    Parameters
    ----------
    bot : hikari.GatewayBot
        The active bot used for getting the endpoint.
    content : str
        The content of the webhook message.
    webhook_id : int
        The Snowflake ID for the webhook. This is the short numerical part in a
        wehook URL.
    webhook_token : str
        The token for the webhook. This is the long final bit in a webhook URL.
    max_content_len : int, optional
        The maximum content length to error out by, by default 2000
    """
    if len(content) > max_content_len:
        # We arbitrarily cut the output to a three-times smaller size, since
        # filling all 2000 characters looks really spammy even if the rest is
        # truncated.
        content = content[: (max_content_len // 3)] + "... and more updates."

    await bot.rest.execute_webhook(
        webhook=webhook_id,
        token=webhook_token,
        username="CompSoc AoC",
        avatar_url="https://img.freepik.com/free-vector/vintage-christmas-tree-with-gifts_23-2148759404.jpg?w=2000",
        mentions_everyone=False,
        user_mentions=False,
        content=content,
    )


def display_aoc_user(mapping_file: str, aoc_user: Any) -> str:
    """Pretty-print an AoC User object in the parsed API response.

    Parameters
    ----------
    mapping_file : str
        The path to the username mapping file, containing JSON keyed by AoC user
        id.
    aoc_user : Any
        The AoC User object in the parsed API response, where some notable keys
        include "name", "id", "completion_day_level", and "last_star_ts".

    Returns
    -------
    str
        A pretty-printed Discord-ready AoC user tag.
    """
    try:
        with open(mapping_file, "r") as f:
            mapping: dict[str, str] = json.load(f)
            return f"<@{mapping[str(aoc_user['id'])]}>"

    except (KeyError, FileNotFoundError, json.decoder.JSONDecodeError):
        return aoc_user.get("name", "Unknown User")


@component.with_schedule
@tanjun.as_time_schedule(minutes=[0, 15, 30, 45, 52])
async def on_schedule(
    cli_args: argparse.Namespace = tanjun.inject(type=argparse.Namespace),
    bot: hikari.GatewayBot = tanjun.inject(type=hikari.GatewayBot),
) -> None:
    old_leaderboard = retrieve_cached_leaderboard(cache_file=cli_args.cache_file)
    new_leaderboard = fetch_leaderboard(
        leaderboard_id=cli_args.leaderboard_id,
        session_id=cli_args.session_id,
        year=cli_args.year,
    )

    old_events = get_leaderboard_set(
        old_leaderboard, require_both=cli_args.require_both_stars
    )
    new_events = get_leaderboard_set(
        new_leaderboard, require_both=cli_args.require_both_stars
    )

    # Get the interesting diff, which only takes into account relevant parameters
    diff = sorted(new_events - old_events)

    if not diff:
        # Either no change, or negative change.
        if old_events == new_events:
            # No change whatsoever since last run.
            return

        # There are negative changes. The only case I can think of that can
        # make this happen is when the year changes.
        # We make a backup keyed with the current time just in case.
        os.replace(
            cli_args.cache_file,
            cli_args.cache_file + datetime.now().strftime(".%H.%M.%S.backup"),
        )
        save_cached_leaderboard(new_leaderboard, cache_file=cli_args.cache_file)
        return

    messages = [
        "[{}] {} solved Day #{}.".format(
            "﹡﹡" if part == "2" else "﹡　",
            display_aoc_user(
                mapping_file=cli_args.mapping_file,
                aoc_user=new_leaderboard["members"][member_id],
            ),
            day,
        )
        for member_id, day, part in diff
    ]

    await send_webhook_notification(
        bot=bot,
        content="\n".join(messages),
        webhook_id=cli_args.webhook_id,
        webhook_token=cli_args.webhook_token,
    )

    save_cached_leaderboard(new_leaderboard, cache_file=cli_args.cache_file)


load_leaderboard = component.make_loader()
