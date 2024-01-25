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

# direwolf.conf
ADEVICE plughw:1,0
ARATE 48000
MODEM 1200 1200:2200

# MODEM 9600
# MODEM 300 2130:2230 D
# PTT GPIO 21
# DWAIT 0
# SLOTTIME 12
# PERSIST 63
# TXDELAY 40
# TXTAIL 10
# FIX_BITS 1 AX25






direwolf -d x -t 0 -X 1