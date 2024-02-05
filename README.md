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
usage: chatfx [-h] [-c CALLSIGN] [-k HOST] [-p PORT] [-t TIME_DELAY] [-s SETTINGS_FILE] [--lf LOG_FILE] [--ll {notset,debug,info,warning,error,critical}]
              [--la {true,false}] [-v]

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
  -v, --verbose         Give more CLI output. Option is additive, and can be used up to 3 times. default=0
```

Using a settings file is an alternative to providing the settings at the command line. The settings file should be stored in the `$XDG_CONFIG_HOME/chatfx` (typically `/home/username/.config/chatfx`) and called `settings.toml`.

A sample settings file follows:

```toml
callsign = "RB1"
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
ABCD = AliceBlue
BCDE = AntiqueWhite
```

The available colors are provided below:

```
AliceBlue
AntiqueWhite
Aqua
Aquamarine
Azure
Beige
Bisque
Black
BlanchedAlmond
Blue
BlueViolet
Brown
BurlyWood
CadetBlue
Chartreuse
Chocolate
Coral
CornflowerBlue
Cornsilk
Crimson
Cyan
DarkBlue
DarkCyan
DarkGoldenRod
DarkGray
DarkGreen
DarkGrey
DarkKhaki
DarkMagenta
DarkOliveGreen
DarkOrange
DarkOrchid
DarkRed
DarkSalmon
DarkSeaGreen
DarkSlateBlue
DarkSlateGray
DarkTurquoise
DarkViolet
DeepPink
DeepSkyBlue
DimGray
DimGrey
DodgerBlue
FireBrick
FloralWhite
ForestGreen
Fuchsia
Gainsboro
GhostWhite
Gold
GoldenRod
Gray
Green
GreenYellow
Grey
HoneyDew
HotPink
IndianRed
Indigo
Ivory
Khaki
Lavender
LavenderBlush
LawnGreen
LemonChiffon
LightBlue
LightCoral
LightCyan
LightGoldenRodYellow
LightGray
LightGreen
LightGrey
LightPink
LightSalmon
LightSeaGreen
LightSkyBlue
LightSlateGray
LightSteelBlue
LightYellow
Lime
LimeGreen
Linen
Magenta
Maroon
MediumAquaMarine
MediumBlue
MediumOrchid
MediumPurple
MediumSeaGreen
MediumSlateBlue
MediumSpringGreen
MediumTurquoise
MediumVioletRed
MidnightBlue
MintCream
MistyRose
Moccasin
NavajoWhite
Navy
OldLace
Olive
OliveDrab
Orange
OrangeRed
Orchid
PaleGoldenRod
PaleGreen
PaleTurquoise
PaleVioletRed
PapayaWhip
PeachPuff
Peru
Pink
Plum
PowderBlue
Purple
RebeccaPurple
Red
RosyBrown
RoyalBlue
SaddleBrown
Salmon
SandyBrown
SeaGreen
SeaShell
Sienna
Silver
SkyBlue
SlateBlue
SlateGray
Snow
SpringGreen
SteelBlue
Tan
Teal
Thistle
Tomato
Turquoise
Violet
Wheat
White
WhiteSmoke
Yellow
YellowGreen
```

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
