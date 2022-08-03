#!/usr/bin/env bash
# Post install script for the UI .deb to place symlinks in places to allow the CLI to work similarly in both versions

set -e

ln -s /usr/lib/joker-blockchain/resources/app.asar.unpacked/daemon/joker /usr/bin/joker || true
ln -s /usr/lib/joker-blockchain/resources/app.asar.unpacked/daemon /opt/joker || true
