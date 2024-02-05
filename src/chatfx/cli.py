"""Chat client for AX.25 packet radio networks."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from pathlib import Path

import tomllib

from .chat import Chat
from .definitions import Config
from .output import Output
from .utils import TermFeatures


def arg_parser() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Chatfx - Chat client for AX.25 packet radio networks.",
    )
    parser.add_argument(
        "-c",
        "--callsign",
        dest="callsign",
        help="Your callsign",
    )
    parser.add_argument(
        "-k",
        "--kiss-host",
        dest="host",
        help="The kiss host. default=localhost",
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        help="The port on the kiss host. default=8001",
    )
    parser.add_argument(
        "-t",
        "--time-delay",
        dest="time_delay",
        help="Time delay between transmissions in seconds. default=2",
    )
    parser.add_argument(
        "-s",
        "--settings-file",
        default=argparse.SUPPRESS,
        dest="settings_file",
        help="Settings file. default=~/config/chatfx/settings.toml",
    )
    parser.add_argument(
        "--lf",
        "--log-file <file>",
        dest="log_file",
        help="Log file to write to. default=./chatfx.log.",
    )
    parser.add_argument(
        "--ll",
        "--log-level <level>",
        dest="log_level",
        choices=["notset", "debug", "info", "warning", "error", "critical"],
        help="Log level for file output. default=debug",
    )
    parser.add_argument(
        "--la",
        "--log-append <bool>",
        dest="log_append",
        choices=["true", "false"],
        help="Append to log file. default=false",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Give more CLI output. Option is additive, and can be used up to 3 times. default=0",
    )
    return parser.parse_args()


def main() -> None:
    """Run the chat client."""
    args = vars(arg_parser())

    try:
        settings_file = Path(args["settings_file"])
        user_provided = True
    except KeyError:
        xdg_cache = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        settings_file = xdg_cache / "chatfx" / "settings.toml"
        user_provided = False

    settings = {}
    try:
        with settings_file.open(mode="rb") as f:
            settings = tomllib.load(f)
    except FileNotFoundError:
        if user_provided:
            print("User provided settings file does not exist.")  # noqa: T201
            sys.exit(1)
    except tomllib.TOMLDecodeError:
        print("Settings file is corrupted.")  # noqa: T201
        sys.exit(1)

    config = Config(
        callsign=args.get("callsign") or settings.get("callsign", None),
        colors=settings.get("colors", {}),
        host=args.get("host") or settings.get("host", "localhost"),
        log_file=args.get("log_file") or settings.get("log-file", Path.cwd() / "chatfx.log"),
        log_level=args.get("log_level") or settings.get("log-level", "info"),
        log_append=args.get("log_append") or settings.get("log-append", "false"),
        port=args.get("port") or settings.get("port", 8001),
        time_delay=float(args.get("time_delay") or settings.get("time-delay", 3)),
        verbose=args.get("verbose") or settings.get("verbose", 1),
    )

    output = Output(
        log_file=config.log_file,
        log_level=config.log_level,
        log_append=config.log_append,
        term_features=TermFeatures(color=True, links=True),
        verbosity=config.verbose,
    )
    output.debug("Starting chat client...")
    output.debug(f"Configuration: {config}")
    if config.callsign is None:
        output.error("You must provide a callsign.")
        sys.exit(1)
    chat = Chat(
        config=config,
        output=output,
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(chat.build_device())
    loop.run_until_complete(chat.run())
    loop.close()


if __name__ == "__main__":
    main()
