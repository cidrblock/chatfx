podman run -it \
    -v ~/direwolf.conf:/etc/direwolf.conf \
    -v ~/.config/chatfx/settings.toml:/etc/chatfx.toml \
    --tz=local \
    --device /dev/snd --device /dev/bus/usb \
    chatfx:latest