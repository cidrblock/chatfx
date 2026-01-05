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
    parser.add_argument(
        "--connection-type",
        dest="connection_type",
        choices=["tcp", "serial", "bluetooth"],
        help="Connection type for KISS TNC. default=tcp",
    )
    parser.add_argument(
        "--bluetooth-address",
        dest="bluetooth_address",
        help="Bluetooth device MAC address (e.g., AA:BB:CC:DD:EE:FF)",
    )
    parser.add_argument(
        "--bluetooth-name",
        dest="bluetooth_name",
        help="Bluetooth device name for auto-discovery",
    )
    parser.add_argument(
        "--baudrate",
        dest="baudrate",
        type=int,
        help="Serial port baudrate for KISS TNC. default=9600",
    )
    parser.add_argument(
        "--serial-device",
        dest="serial_device",
        help="Serial device path (e.g., /dev/rfcomm0 or COM3)",
    )
    return parser.parse_args()
