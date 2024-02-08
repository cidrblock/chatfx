"""Command line argument parser for Chatfx."""

from __future__ import annotations

import argparse


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
