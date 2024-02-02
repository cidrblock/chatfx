# chatfx

A simple chat application using FX.25.

## Direwolf

Install direwolf (fedora)

```
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
ARATE 48000
MODEM 1200 1200:2200
```
The `ADEVICE` refers to the soundcard found using `aplay`

Run direwolf
```
direwolf -t 0 -X 1
```

for more verbose output from direwolf

```
direwolf -d x -t 0 -X 1
```



## Colors

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