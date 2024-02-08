"""Run the chatfx application."""
import asyncio
import os
import sys

from pathlib import Path

import tomllib

from chatfx.arg_parse import arg_parser
from chatfx.chat import Chat
from chatfx.definitions import Config
from chatfx.definitions import TermFeatures
from chatfx.output import Output
from chatfx.ui import Ui
from chatfx.ui import run as run_ui


async def log_startup(output: Output, config: Config) -> None:
    """Log the startup of the chatfx application."""
    output.debug("Starting chatfx application.")
    output.debug(f"Configuration: {config}")


async def start() -> None:
    """Start the chatfx application."""
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
        verbose=args.get("verbose") or settings.get("verbose", 0),
    )

    ui = Ui()
    ui.init()

    output = Output(
        log_file=config.log_file,
        log_level=config.log_level,
        log_append=config.log_append,
        term_features=TermFeatures(color=True, links=True),
        verbosity=config.verbose,
        ui_output=ui.output,
        ui_refresh=ui.refresh,
    )
    if config.callsign is None:
        output.error("You must provide a callsign.")
        sys.exit(1)

    chat = Chat(
        config=config,
        output=output,
        ui_output=ui.output,
        ui_refresh=ui.refresh,
    )
    ui.chat_send = chat.send

    loop = asyncio.get_event_loop()
    await chat.build_device()

    log_start = loop.create_task(log_startup(output=output, config=config))
    ui_task = loop.create_task(run_ui(output=output, ui=ui))
    chat_task = loop.create_task(chat.run())
    await asyncio.gather(log_start, ui_task, chat_task)


def main() -> None:
    """Run the chatfx application."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_task = loop.create_task(start())
    loop.run_until_complete(asyncio.gather(start_task))
    loop.close()


if __name__ == "__main__":
    main()
