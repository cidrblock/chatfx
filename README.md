# chatfx

A simple chat application using FX.25.

## Installation

```
pip install https://github.com/cidrblock/chatfx
```

## Quick start

```
chatfx -c MYCALL
> YOURCALL hello world
```

## Usage

The application settings can be provided on the command line or with a settings file.

The command line parameters can be found using `--help`.

```
$ chatfx --help
usage: chatfx [-h] [-c CALLSIGN] [-k HOST] [-p PORT] [-t TIME_DELAY] [-s SETTINGS_FILE] 
              [--lf LOG_FILE] [--ll {notset,debug,info,warning,error,critical}]
              [--la {true,false}] [--connection-type {tcp,serial,bluetooth}]
              [--bluetooth-address BLUETOOTH_ADDRESS] [--bluetooth-name BLUETOOTH_NAME]
              [--baudrate BAUDRATE] [--serial-device SERIAL_DEVICE] [-v]

Chatfx - Chat client for AX.25 packet radio networks.

options:
  -h, --help            show this help message and exit
  -c CALLSIGN, --callsign CALLSIGN
                        Your callsign
  -k HOST, --kiss-host HOST
                        The kiss host. default=localhost
  -p PORT, --port PORT  The port on the kiss host. default=8001
  -t TIME_DELAY, --time-delay TIME_DELAY
                        Time delay between transmissions in seconds. default=2
  -s SETTINGS_FILE, --settings-file SETTINGS_FILE
                        Settings file. default=~/config/chatfx/settings.toml
  --lf LOG_FILE, --log-file <file> LOG_FILE
                        Log file to write to. default=./chatfx.log.
  --ll {notset,debug,info,warning,error,critical}, --log-level <level> {notset,debug,info,warning,error,critical}
                        Log level for file output. default=debug
  --la {true,false}, --log-append <bool> {true,false}
                        Append to log file. default=false
  --connection-type {tcp,serial,bluetooth}
                        Connection type for KISS TNC. default=tcp
  --bluetooth-address BLUETOOTH_ADDRESS
                        Bluetooth device MAC address (e.g., AA:BB:CC:DD:EE:FF)
  --bluetooth-name BLUETOOTH_NAME
                        Bluetooth device name for auto-discovery
  --baudrate BAUDRATE   Serial port baudrate for KISS TNC. default=9600
  --serial-device SERIAL_DEVICE
                        Serial device path (e.g., /dev/rfcomm0 or COM3)
  -v, --verbose         Give more CLI output. Option is additive, and can be used up to 3 times. default=0
```

### Connection Types

**TCP (default)** - Connect to a KISS TNC via TCP (e.g., direwolf)
```bash
chatfx -c MYCALL -k localhost -p 8001
```

**Serial** - Connect to a KISS TNC via serial port
```bash
chatfx -c MYCALL --connection-type serial --serial-device /dev/ttyUSB0 --baudrate 9600
```

**Bluetooth** - Connect to a Bluetooth KISS TNC (e.g., BTECH UV-PRO)
```bash
# Using MAC address (recommended for headless systems)
chatfx -c MYCALL --connection-type bluetooth --bluetooth-address AA:BB:CC:DD:EE:FF

# Using device name (auto-discovery)
chatfx -c MYCALL --connection-type bluetooth --bluetooth-name "UV-PRO"
```

### Settings File

Using a settings file is an alternative to providing the settings at the command line. The settings file should be stored in the `$XDG_CONFIG_HOME/chatfx` (typically `/home/username/.config/chatfx`) and called `settings.toml`.

A sample settings file for TCP (direwolf) follows:

```toml
callsign = "RB1"
host = "localhost"
port = 8001
log-file = "/tmp/chatfx.log"
log-append = "false"
log-level = "debug"
time-delay = 2
verbose = 3


[colors]
rb1 = "Aqua"
rb2 = "YellowGreen"
```

A sample settings file for Bluetooth (headless) follows:

```toml
callsign = "MYCALL"
connection-type = "bluetooth"
bluetooth-address = "AA:BB:CC:DD:EE:FF"
baudrate = 9600
log-file = "/tmp/chatfx.log"
log-level = "debug"
time-delay = 2
verbose = 3

[colors]
mycall = "Aqua"
```

Note: See the colors section below for a description of the colors section.

## Direwolf

Install direwolf (fedora)

```bash
sudo usermod -a -G audio <your account>

sudo dnf install git gcc gcc-c++ make alsa-lib-devel libudev-devel avahi-devel cmake3 -y

mkdir ~/github
cd ~/github
git clone https://www.github.com/wb2osz/direwolf
cd direwolf
mkdir build && cd build
cmake ..
make -j4
sudo make install
make install-conf
```

Add a ~/direwolf.conf

```
ADEVICE plughw:1,0
CHANNEL 0
ARATE 48000
DWAIT 10
IL2PTX +1
MODEM 1200 1200:2200
PTT CM108
TXDELAY 60
```

The `ADEVICE` refers to the soundcard found using `aplay`

Run direwolf

```
direwolf -t 0 -X 1
```

for more verbose output from direwolf

```
direwolf -d x2o -t 0 -q d
```

## Colors

Terminal output can be colored based on both sender and receiver callsign. The color mapping cannot be provided on the command line and needs to be provided in the settings file. Each line in the `colors` sections of the settings file is a mapping between call sign and terminal color.

Sample:

```toml
[colors]
ABCD = "aliceblue"
BCDE = "antiquewhite"
```

The color list can be found here: https://www.w3schools.com/colors/colors_names.asp. Color names should be lowercase in the settings.file.

## Payload format

Byte 0

- PID (No Layer 3 protocol)

Byte 1

- 2 bits - Message type
- 2 bits - Compression type
- 4 bits - Reserved

Bytes 2-3

- 16 bits - Message ID

Bytes 4+

- nn bytes - Message

## Other notes

To disable HUD for a USB to audio adapter

```
lsusb
lsusb -t
sudo more /sys/bus/usb/devices/1-12/1-12:1.3/authorized
sudo vi /etc/udev/rules.d/99-usb-audio.rules
ACTION=="add", ATTR{idVendor}=="001f", ATTR{idProduct}=="0b21", RUN+="/bin/sh -c 'echo 0 > /sys$DEVPATH/`basename $DEVPATH`:1.3/authorized'"
```

To disable gdm sleep

```
sudo -u gdm dbus-run-session gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
```

## Bluetooth KISS TNC Setup

For headless Bluetooth operation (e.g., BTECH UV-PRO), the application can automatically discover and connect to Bluetooth devices.

### Prerequisites

Install PyBluez for Bluetooth support:

```bash
# Fedora/RHEL
sudo dnf install python3-bluez bluez-libs-devel

# Debian/Ubuntu
sudo apt-get install python3-bluez libbluetooth-dev

# Install via pip
pip install pybluez
```

### Headless Configuration

For fully automatic headless operation, you can either:

1. **Use MAC address** (recommended for headless systems):
   ```bash
   chatfx -c MYCALL --connection-type bluetooth --bluetooth-address AA:BB:CC:DD:EE:FF
   ```

2. **Use device name** (auto-discovery):
   ```bash
   chatfx -c MYCALL --connection-type bluetooth --bluetooth-name "UV-PRO"
   ```

3. **Pre-configure /dev/rfcomm device** (Linux only):
   
   Create `/etc/bluetooth/rfcomm.conf`:
   ```
   rfcomm0 {
       bind yes;
       device AA:BB:CC:DD:EE:FF;
       channel 1;
       comment "BTECH UV-PRO";
   }
   ```
   
   Then use:
   ```bash
   chatfx -c MYCALL --connection-type serial --serial-device /dev/rfcomm0
   ```

### Finding Your Bluetooth Device

To find your device's MAC address:

```bash
# Linux
bluetoothctl
scan on
# Wait for devices to appear, note the MAC address
scan off
exit

# Or use the Python script
python3 -c "import bluetooth; print(bluetooth.discover_devices(lookup_names=True))"
```

### Troubleshooting Bluetooth

**Permission denied errors:**
```bash
# Add your user to the bluetooth group
sudo usermod -a -G bluetooth $USER
# Log out and back in
```

**Device not found:**
- Ensure the device is powered on and in pairing mode
- Check that Bluetooth is enabled: `bluetoothctl power on`
- Try manual discovery: `bluetoothctl scan on`

**Connection refused:**
- The device may need to be paired first via `bluetoothctl pair AA:BB:CC:DD:EE:FF`
- Some devices require trust: `bluetoothctl trust AA:BB:CC:DD:EE:FF`

**For Raspberry Pi headless setup:**
```bash
# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Auto-reconnect on boot (systemd service)
sudo vi /etc/systemd/system/chatfx-bluetooth.service
```

Example systemd service:
```ini
[Unit]
Description=ChatFX Bluetooth KISS TNC
After=bluetooth.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/chatfx -c MYCALL --connection-type bluetooth --bluetooth-address AA:BB:CC:DD:EE:FF
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

