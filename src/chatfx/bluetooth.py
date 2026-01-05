"""Bluetooth connection management for headless operation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .output import Output

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False


class BluetoothConnection:
    """Manage Bluetooth connections for headless operation."""

    def __init__(
        self: BluetoothConnection,
        output: Output,
        address: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize Bluetooth connection manager.

        Args:
            output: Output handler for logging
            address: Bluetooth MAC address (e.g., 'AA:BB:CC:DD:EE:FF')
            name: Bluetooth device name for discovery
        """
        if not BLUETOOTH_AVAILABLE:
            msg = "PyBluez not installed. Install with: pip install pybluez"
            raise ImportError(msg)

        self.output = output
        self.address = address
        self.name = name
        self.rfcomm_channel = 1  # Default RFCOMM channel for SPP

    def discover_device(self: BluetoothConnection) -> str | None:
        """Discover Bluetooth device by name.

        Returns:
            MAC address of discovered device or None
        """
        self.output.info("Discovering Bluetooth devices...")
        nearby_devices = bluetooth.discover_devices(
            duration=8,
            lookup_names=True,
            flush_cache=True,
        )

        for addr, device_name in nearby_devices:
            self.output.debug(f"Found device: {device_name} [{addr}]")
            if self.name and self.name.lower() in device_name.lower():
                self.output.info(f"Found target device: {device_name} [{addr}]")
                return addr

        return None

    def find_rfcomm_channel(self: BluetoothConnection, address: str) -> int | None:
        """Find RFCOMM channel for SPP service on device.

        Args:
            address: Bluetooth MAC address

        Returns:
            RFCOMM channel number or None
        """
        self.output.debug(f"Looking for SPP service on {address}")
        services = bluetooth.find_service(address=address)

        for svc in services:
            if "Serial" in svc.get("name", "") or "SPP" in svc.get("name", ""):
                channel = svc.get("port")
                self.output.info(f"Found SPP service on channel {channel}")
                return channel

        # Default to channel 1 if no service found
        self.output.debug("No SPP service found, using default channel 1")
        return 1

    def create_rfcomm_socket(self: BluetoothConnection) -> bluetooth.BluetoothSocket:
        """Create and connect RFCOMM socket.

        Returns:
            Connected Bluetooth socket

        Raises:
            ConnectionError: If connection fails
        """
        # Get device address
        if not self.address and self.name:
            self.output.info(f"Searching for device: {self.name}")
            self.address = self.discover_device()
            if not self.address:
                msg = f"Could not find device: {self.name}"
                raise ConnectionError(msg)

        if not self.address:
            msg = "No Bluetooth address or device name provided"
            raise ValueError(msg)

        # Find RFCOMM channel
        self.rfcomm_channel = self.find_rfcomm_channel(self.address) or 1

        # Create socket
        self.output.info(f"Connecting to {self.address} on channel {self.rfcomm_channel}")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

        try:
            sock.connect((self.address, self.rfcomm_channel))
        except bluetooth.BluetoothError as e:
            msg = f"Failed to connect to Bluetooth device: {e}"
            raise ConnectionError(msg) from e
        else:
            self.output.info("Bluetooth connection established")
            return sock

    def get_serial_port_path(self: BluetoothConnection) -> str:
        """Get path to virtual serial port for this Bluetooth connection.

        This method attempts to bind the Bluetooth device to /dev/rfcomm0.
        For headless operation, this should be configured at system level.

        Returns:
            Path to serial device (e.g., '/dev/rfcomm0')

        Raises:
            NotImplementedError: Direct binding not implemented
        """
        # For true headless operation, the system should have rfcomm
        # pre-configured via /etc/bluetooth/rfcomm.conf or systemd
        # This is a placeholder for future implementation
        msg = (
            "Direct RFCOMM binding not implemented. "
            "Please configure /dev/rfcomm0 via system tools or "
            "use connection_type='bluetooth' for direct socket connection."
        )
        raise NotImplementedError(msg)


def ensure_bluetooth_connected(
    output: Output,
    address: str | None = None,
    name: str | None = None,
) -> str | bluetooth.BluetoothSocket:
    """Ensure Bluetooth device is connected for headless operation.

    Args:
        output: Output handler for logging
        address: Bluetooth MAC address
        name: Bluetooth device name

    Returns:
        Either serial port path or Bluetooth socket

    Raises:
        ConnectionError: If connection fails
    """
    bt_conn = BluetoothConnection(output, address, name)

    # Try to find existing serial port binding first
    # In production, this should be set up via system configuration
    for i in range(10):
        rfcomm_path = Path(f"/dev/rfcomm{i}")
        if rfcomm_path.exists():
            output.info(f"Found existing RFCOMM device: {rfcomm_path}")
            return str(rfcomm_path)

    # If no existing binding, create direct socket connection
    output.info("No existing RFCOMM device found, creating direct connection")
    return bt_conn.create_rfcomm_socket()
