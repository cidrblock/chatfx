podman run -it \
    -v ~/direwolf.conf:/etc/direwolf.conf \
    -v ~/.config/chatfx/settings.toml:/etc/chatfx.toml \
    --device /dev/snd --device /dev/bus/usb \
    radio 