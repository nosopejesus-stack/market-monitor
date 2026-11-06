#!/bin/bash
# Start a virtual X11 desktop with an AT-SPI accessibility bus, then run the given command inside it.
export DISPLAY=:99 XDG_RUNTIME_DIR=/tmp/xdg-run NO_AT_BRIDGE=0 GTK_A11Y=atspi
mkdir -p $XDG_RUNTIME_DIR && chmod 700 $XDG_RUNTIME_DIR
pgrep -x Xvfb >/dev/null || (Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 1
exec dbus-run-session -- bash -c '
  /usr/libexec/at-spi-bus-launcher --launch-immediately >/dev/null 2>&1 &
  sleep 2
  '"$*"'
'
